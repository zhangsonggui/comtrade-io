from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_serializer

from .channel.analog import Analog
from .channel.status import Status, StatusChangeRecord
from .configure import Configure
from .description.channel_num import ChannelNum
from .description.header import Header
from .description.sampling import Sampling
from .description.sampling_time_quality import SamplingTimeQuality
from .description.time_info import TimeInfo
from .equipment import Bus, EquipmentGroup, Line, Transformer
from .type import DataType
from ..exporters.decorators import export_format
from ..exporters.json_exporter import _to_json
from ..utils import get_logger

if TYPE_CHECKING:
    from ..parser.comtrade_file import ComtradeFile

logger = get_logger()


class Comtrade(BaseModel):
    """COMTRADE 数据模型

    包含 COMTRADE 故障录波文件的完整信息：

    配置信息（通过 cfg 属性访问）:
        cfg.header: 文件头（厂站名、录波器名、版本号）
        cfg.channel_num: 通道数量定义（模拟量/数字量各多少）
        cfg.analogs: 模拟量通道定义字典（编号 → Analog 对象）
        cfg.statuses: 数字量通道定义字典（编号 → Status 对象）
        cfg.sampling: 采样信息（频率、采样率分段）
        cfg.start_time: 录波开始时间
        cfg.fault_time: 故障触发时间
        cfg.data_type: 数据格式（ASCII/BINARY/BINARY32/FLOAT32）
        cfg.timemult: 时间乘数

    本类扩展:
        file: 文件路径信息（CFG/DAT/INF/DMF 各路径）
        data: 录波数据（DataFrame 格式，每列对应一个通道）
        description: 描述信息（用于 DMF/INF 导出）
        buses: 母线列表（设备拓扑）
        lines: 线路列表（设备拓扑）
        transformers: 变压器列表（设备拓扑）
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    config: Configure = Field(default_factory=Configure, description="CFG配置")
    data: pd.DataFrame | None = Field(default=None, description="故障数据")
    buses: list[Bus] | None = Field(default_factory=list, description="母线")
    lines: list[Line] | None = Field(default_factory=list, description="线路")
    transformers: list[Transformer] | None = Field(
        default_factory=list, description="变压器"
    )

    # -- 向后兼容属性：委托到 cfg --

    @property
    def analogs(self) -> dict[int, Analog]:
        return self.config.analogs

    @property
    def statuses(self) -> dict[int, Status]:
        return self.config.statuses

    @property
    def channel_num(self) -> ChannelNum | None:
        return self.config.description.channel_num

    @property
    def sampling(self) -> Sampling | None:
        return self.config.description.sampling

    @property
    def start_time(self) -> datetime | None:
        return self.config.description.file_start_time

    @property
    def fault_time(self) -> datetime | None:
        return self.config.description.trigger_time

    @property
    def data_type(self) -> DataType | None:
        return self.config.description.data_type

    @property
    def timemult(self) -> float | None:
        return self.config.description.timemult

    @property
    def header(self) -> Header | None:
        return self.config.description.header

    @property
    def time_info(self) -> TimeInfo | None:
        return self.config.description.time_info

    @property
    def sampling_time_quality(self) -> SamplingTimeQuality | None:
        return self.config.description.sampling_time_quality

    # -- 序列化 --

    @model_serializer(mode="wrap")
    def serialize_model(self, handler, info):
        data = handler(self)
        data.pop("cfg", None)
        if self.config:
            mode = "json" if info.mode == "json" else "python"
            cfg_data = self.config.model_dump(mode=mode)
            data.update(cfg_data)
        return data

    def model_dump_json(self, *, indent: int | None = None, **kwargs) -> str:
        data = self.model_dump(mode="python")
        data.pop("data", None)
        data.pop("file", None)
        return _to_json(data, indent)

    # -- 数据访问 --

    def get_data(self) -> pd.DataFrame:
        return self.data

    def get_analog_channel(self, index: int) -> Analog | None:
        analog = self.get_analog_channel_info(index)
        if analog is None or self.data is None:
            return None
        analog.data = self.data.iloc[:, index + 1].to_numpy()
        return analog

    def get_status_channel(self, index: int) -> Status | None:
        digital = self.get_status_channel_info(index)
        if digital is None or self.data is None:
            return None
        digital.data = self.data.iloc[:, index + self.channel_num.analog + 1].to_numpy()
        return digital

    def _load_status_data(self, channels: list, data: pd.DataFrame):
        for chn in channels:
            if chn and chn.index is not None:
                col_index = self.channel_num.analog + chn.index + 1
                chn.data = (
                    data.iloc[:, col_index].to_numpy()
                    if col_index < data.shape[1]
                    else None
                )

    @staticmethod
    def _load_analog_channels(channels: tuple, data: pd.DataFrame):
        for chn in channels:
            if chn:
                col_index = chn.index + 1
                chn.data = (
                    data.iloc[:, col_index].to_numpy()
                    if col_index < data.shape[1]
                    else None
                )

    # -- 设备拓扑查询 --

    def get_line(self, name: str) -> Line | None:
        line = self.get_line_info(name)
        if line is None or self.data is None:
            return line

        data = self.data
        for current in line.currents:
            self._load_analog_channels(current.current_tuple, data)

        for bus in line.buses:
            self._load_analog_channels(bus.voltage.voltage_tuple, data)

        self._load_status_data(line.stas, data)

        return line

    def get_bus(self, name: str) -> Bus | None:
        bus = self.get_bus_info(name)
        if bus is None or self.data is None:
            return bus

        data = self.data
        self._load_analog_channels(bus.voltage.voltage_tuple, data)

        self._load_status_data(bus.anas, data)
        self._load_status_data(bus.stas, data)

        return bus

    def get_transformer(self, name: str) -> Transformer | None:
        transformer = self.get_transformer_info(name)
        if transformer is None or self.data is None:
            return transformer

        data = self.data
        for winding in transformer.trans_winds:
            self._load_analog_channels(winding.voltage.voltage_tuple, data)
            for current in winding.currents:
                self._load_analog_channels(current.current_tuple, data)

        self._load_status_data(transformer.anas, data)
        self._load_status_data(transformer.stas, data)

        return transformer

    def from_equipment_group(self, eg: EquipmentGroup):
        self.buses = eg.buses
        self.lines = eg.lines
        self.transformers = eg.transformers
        for idx, analog in eg.analogs.items():
            analog_model = self.analogs.get(idx)
            if analog_model:
                analog_model.sync_from(analog)
        for idx, status in eg.statuses.items():
            status_model = self.statuses.get(idx)
            if status_model:
                status_model.sync_from(status)

    def generate_equipment_group(self):
        """根据通道配置生成设备拓扑（占位方法）

        可以通过通道的名称/相别信息自动推断母线、线路拓扑结构。
        当前为占位方法，子类可覆盖实现具体逻辑。
        """

    def get_bus_info(self, name: str) -> Bus | None:
        if self.buses is None:
            return None
        return next((bus for bus in self.buses if bus.name == name), None)

    def get_line_info(self, name: str) -> Line | None:
        if self.lines is None:
            return None
        return next((line for line in self.lines if line.name == name), None)

    def get_transformer_info(self, name: str) -> Transformer | None:
        if self.transformers is None:
            return None
        return next((trans for trans in self.transformers if trans.name == name), None)

    def get_analog_channel_info(self, index: int) -> Analog | None:
        if self.analogs is None:
            return None
        return self.analogs.get(index)

    def get_status_channel_info(self, index: int) -> Status | None:
        if self.statuses is None:
            return None
        return self.statuses.get(index)

    def get_changed_statuses(self) -> list[Status]:
        """获取发生变位的数字量通道

        使用 numpy 向量化计算逐通道的状态跳变，筛选出存在变位的数字量通道，
        并在每个 Status 对象上填充 change_records 变位记录列表：
        - 首条为 0 时刻（第 1 个采样点）的初始状态；
        - 后续每条对应一次变位时刻的采样点号、时间戳、状态。

        Returns:
            list[Status]: 发生变位的数字量通道列表（数据为空或无变位时返回空列表）
        """
        if self.data is None or self.channel_num is None or not self.statuses:
            return []

        data = self.data
        n_rows = data.shape[0]
        if n_rows == 0:
            return []

        timestamps_us = data.iloc[:, 1].to_numpy(dtype=np.int64)
        start_time = self.start_time

        def _timestamp_at(sample_idx: int) -> datetime | None:
            if start_time is None or sample_idx < 0 or sample_idx >= n_rows:
                return None
            return start_time + timedelta(microseconds=int(timestamps_us[sample_idx]))

        analog_count = self.channel_num.analog
        changed: list[Status] = []
        for status in self.statuses.values():
            if status is None or status.index is None:
                continue
            col_index = analog_count + status.index + 1
            if col_index >= data.shape[1]:
                continue

            values = data.iloc[:, col_index].to_numpy(dtype=np.int8)
            if values.size == 0:
                continue

            initial_state = int(values[0])
            records = [
                StatusChangeRecord(
                    sample_point=1,
                    timestamp=_timestamp_at(0),
                    state=initial_state,
                )
            ]

            if values.size > 1:
                diff = np.diff(values.astype(np.int16))
                change_positions = np.nonzero(diff != 0)[0] + 1
                for pos in change_positions:
                    records.append(
                        StatusChangeRecord(
                            sample_point=int(pos) + 1,
                            timestamp=_timestamp_at(int(pos)),
                            state=int(values[int(pos)]),
                        )
                    )

            if len(records) > 1:
                status.change_records = records
                changed.append(status)

        return changed

    # -- 导出 --

    def to_cfg(self):
        return str(self.config)

    def to_dmf(self) -> str:
        attrs = [f"{str(self.config.description.to_dmf())}"]
        for analog in self.analogs.values():
            attrs.append(analog.to_dmf())
        for status in self.statuses.values():
            attrs.append(status.to_dmf())
        for bus in self.buses or []:
            attrs.append(bus.to_dmf())
        for line in self.lines or []:
            attrs.append(line.to_dmf())
        for trans in self.transformers or []:
            attrs.append(trans.to_dmf())
        attrs.append(f"</scl:ComtradeModel>")
        return "\n".join(attrs)

    def to_inf(self) -> str:
        attrs = [self.config.description.to_inf()]

        for analog in self.analogs.values():
            attrs.append(f"\n")
            attrs.append(analog.to_inf())
        for status in self.statuses.values():
            attrs.append(f"\n")
            attrs.append(status.to_inf())

        if self.analogs:
            attrs.append(f"\n")
            attrs.append("[ZYHD Analog_Channels_Parameter]")
            for analog in self.analogs.values():
                attrs.append(f"CHNL_INFO_#{analog.index}={analog.to_inf_parameter()}")

        if self.statuses:
            attrs.append(f"\n")
            attrs.append("[ZYHD Status_Channels_Parameter]")
            for status in self.statuses.values():
                attrs.append(f"CHNL_INFO_#{status.index}={status.to_inf_parameter()}")

        for bus in self.buses or []:
            attrs.append(f"\n")
            attrs.append(bus.to_inf())
        for line in self.lines or []:
            attrs.append(f"\n")
            attrs.append(line.to_inf())
        for transformer in self.transformers or []:
            attrs.append(f"\n")
            attrs.append(transformer.to_inf())
        return "\n".join(attrs)

    def write_cfg(self, path: str) -> None:
        with open(path, "w", encoding="gbk", errors="ignore") as f:
            f.write(str(self.config))

    def write_dmf(self, path: str) -> None:
        with open(path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(self.to_dmf())

    def write_inf(self, path: str) -> None:
        with open(path, "w", encoding="gbk", errors="ignore") as f:
            f.write(self.to_inf())

    @export_format
    def save_comtrade(
        self,
        output_file_path: ComtradeFile | Path | str,
        format: str = "multi_file",
        data_format: str = "BINARY",
        **kwargs,
    ):
        pass
