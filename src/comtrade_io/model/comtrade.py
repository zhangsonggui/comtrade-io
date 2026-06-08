#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_serializer

from comtrade_io.exporters.json_exporter import _to_json
from comtrade_io.model.channel.analog import Analog
from comtrade_io.model.channel.status import Status
from comtrade_io.model.configure import Configure
from comtrade_io.model.equipment import Bus, EquipmentGroup, Line, Transformer
from comtrade_io.utils import get_logger

if TYPE_CHECKING:
    from comtrade_io.parser.comtrade_file import ComtradeFile

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
    def channel_num(self):
        return self.config.description.channel_num

    @property
    def sampling(self):
        return self.config.description.sampling

    @property
    def start_time(self):
        return self.config.description.file_start_time

    @property
    def fault_time(self):
        return self.config.description.trigger_time

    @property
    def data_type(self):
        return self.config.description.data_type

    @property
    def timemult(self):
        return self.config.description.timemult

    @property
    def header(self):
        return self.config.description.header

    @property
    def time_info(self):
        return self.config.description.time_info

    @property
    def sampling_time_quality(self):
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
        if analog is None:
            return None
        analog.data = self.data.iloc[:, index + 1].to_numpy()
        return analog

    def get_status_channel(self, index: int) -> Status | None:
        digital = self.get_status_channel_info(index)
        if digital is None:
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

    # -- 导出 --

    def to_cfg(self):
        return str(self.config)

    def to_dmf(self) -> str:
        attrs = [f"{str(self.config.description.to_dmf())}"]
        for analog in self.analogs.values():
            attrs.append(analog.to_dmf())
        for status in self.statuses.values():
            attrs.append(status.to_dmf())
        for bus in self.buses:
            attrs.append(bus.to_dmf())
        for line in self.lines:
            attrs.append(line.to_dmf())
        for trans in self.transformers:
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

        for bus in self.buses:
            attrs.append(f"\n")
            attrs.append(bus.to_inf())
        for line in self.lines:
            attrs.append(f"\n")
            attrs.append(line.to_inf())
        for transformer in self.transformers:
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

    def save_comtrade(self, output_file_path: ComtradeFile | Path | str, **kwargs):
        pass


# 延迟导入 export_format 装饰器以打破循环导入
from comtrade_io.exporters import export_format  # noqa: E402

Comtrade.save_comtrade = export_format(Comtrade.save_comtrade)  # type: ignore[arg-type]
