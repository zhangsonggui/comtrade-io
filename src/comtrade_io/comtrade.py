#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import Field

from comtrade_io.cff import CffFile
from comtrade_io.cfg import Configure
from comtrade_io.channel.analog import Analog
from comtrade_io.channel.status import Status
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.comtrade_model import ComtradeModel
from comtrade_io.data import DataContent
from comtrade_io.dmf.dmf_element import DmfElement
from comtrade_io.equipment.bus import Bus
from comtrade_io.equipment.equipment_group import EquipmentGroup
from comtrade_io.equipment.line import Line
from comtrade_io.equipment.transformer import Transformer
from comtrade_io.exporters import export_format
from comtrade_io.exporters.json_exporter import _to_json
from comtrade_io.inf import Information
from comtrade_io.utils import get_logger

logging = get_logger()


class Comtrade(ComtradeModel):
    file: ComtradeFile = Field(default_factory=ComtradeFile, description="文件路径")
    dat: Optional[DataContent] = Field(default=None, description="故障数据")

    def model_dump_json(self, *, indent: int | None = None, **kwargs) -> str:
        """
        将Comtrade模型转换为JSON字符串（不包含dat、file字段）
        """
        data = self.model_dump(mode='python')
        data.pop("dat", None)
        data.pop("file", None)
        return _to_json(data, indent)

    def get_data(self) -> pd.DataFrame:
        return self.dat.data

    def get_analog_channel(self, index: int) -> Optional[Analog]:
        """
        根据通道标识获取模拟量通道，并加载通道数据
        """
        analog = self.get_analog_channel_info(index)
        analog.data = self.dat.data.iloc[:, index + 1].to_numpy()
        return analog

    def get_status_channel(self, index: int) -> Optional[Status]:
        """
        根据通道标识获取状态量通道，并加载通道数据
        """
        digital = self.get_status_channel_info(index)
        digital.data = self.dat.data.iloc[:, index + self.channel_num.analog + 1].to_numpy()
        return digital

    def _load_digital_data(self, channels: list, data: pd.DataFrame):
        """加载数字量通道数据到通道对象列表"""
        for chn in channels:
            if chn and chn.index is not None:
                col_index = self.channel_num.analog + chn.index + 1
                chn.data = data.iloc[:, col_index].to_numpy() if col_index < data.shape[1] else None

    @staticmethod
    def _load_analog_channels(channels: tuple, data: pd.DataFrame):
        """加载模拟量通道数据（ia, ib, ic, i0 或 ua, ub, uc, ul, un）"""
        for chn in channels:
            if chn:
                col_index = chn.index + 1
                chn.data = data.iloc[:, col_index].to_numpy() if col_index < data.shape[1] else None

    def get_line(self, name: str) -> Line | None:
        """
        根据名称获取线路，并加载通道数据

        参数:
            name: 线路名称

        返回:
            线路对象，如果未找到则返回None
        """
        line = self.get_line_info(name)
        if line is None or self.dat is None:
            return line

        data = self.dat.data
        if data is None:
            return line

        # 加载电流通道数据
        for current in line.currents:
            self._load_analog_channels((current.ia, current.ib, current.ic, current.i0), data)

        # 加载电压通道数据
        for bus in line.buses:
            self._load_analog_channels((bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.ul, bus.voltage.un),
                                       data)

        # 加载开关量通道数据
        self._load_digital_data(line.stas, data)

        return line

    def get_bus(self, name: str) -> Bus | None:
        """
        根据名称获取母线，并加载通道数据

        参数:
            name: 母线名称

        返回:
            母线对象，如果未找到则返回None
        """
        bus = super().get_bus_info(name)
        if bus is None or self.dat is None:
            return bus

        data = self.dat.data
        if data is None:
            return bus

        # 加载电压通道数据
        self._load_analog_channels((bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.ul, bus.voltage.un),
                                   data)

        # 加载模拟通道和开关量通道数据
        self._load_digital_data(bus.anas, data)
        self._load_digital_data(bus.stas, data)

        return bus

    def get_transformer(self, name: str) -> Transformer | None:
        """
        根据名称获取变压器，并加载通道数据

        参数:
            name: 变压器名称

        返回:
            变压器对象，如果未找到则返回None
        """
        transformer = super().get_transformer_info(name)
        if transformer is None or self.dat is None:
            return transformer

        data = self.dat.data
        if data is None:
            return transformer

        # 加载各绕组的电压和电流通道数据
        for winding in transformer.trans_winds:
            self._load_analog_channels(
                    (winding.voltage.ua, winding.voltage.ub, winding.voltage.uc, winding.voltage.ul,
                     winding.voltage.un),
                    data)
            for current in winding.currents:
                self._load_analog_channels((current.ia, current.ib, current.ic, current.i0), data)

        # 加载模拟通道和开关量通道数据
        self._load_digital_data(transformer.anas, data)
        self._load_digital_data(transformer.stas, data)

        return transformer

    @staticmethod
    def _sync_channels(configure: Configure, comtrade_model: ComtradeModel) -> None:
        """同步Configure和ComtradeModel中的通道信息"""
        for idx, cfg_analog in configure.analogs.items():
            if idx in comtrade_model.analogs:
                cm_analog = comtrade_model.analogs.get(idx)
                cm_analog.sync_from(cfg_analog)

        for idx, cfg_status in configure.statuses.items():
            if idx in comtrade_model.statuses:
                cm_status = comtrade_model.statuses.get(idx)
                cm_status.sync_from(cfg_status)

    @classmethod
    def _create_comtrade(cls,
                         file: ComtradeFile,
                         cfg: Configure,
                         eg: EquipmentGroup = None,
                         dat: DataContent = None) -> "Comtrade":
        """创建Comtrade对象的共享方法"""
        _model = ComtradeModel.from_configure(cfg)
        if eg:
            _model.from_equipment_group(eg)
        else:
            _model.generate_equipment_group()

        return cls.model_construct(
                file=file,
                header=_model.header,
                channel_num=_model.channel_num,
                analogs=_model.analogs,
                statuses=_model.statuses,
                sampling=_model.sampling,
                start_time=_model.start_time,
                fault_time=_model.fault_time,
                data_type=_model.data_type,
                timemult=_model.timemult,
                time_info=_model.time_info,
                sampling_time_quality=_model.sampling_time_quality,
                description=_model.description,
                buses=_model.buses,
                lines=_model.lines,
                transformers=_model.transformers,
                dat=dat,
        )

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> "Comtrade|None":
        """从文件名反序列化Comtrade对象"""
        cf = ComtradeFile.from_path(file_name)

        if cf.cff_path.is_enabled():
            return cls._from_cff(cf)

        configure = Configure.from_file(file_name=cf)
        if configure is None:
            return None

        eg = DmfElement.from_file(file_name=cf)
        if eg is None:
            eg = Information.from_file(file_name=cf)

        data_content = DataContent(cfg=configure, file_name=cf)
        return cls._create_comtrade(file=cf, cfg=configure, eg=eg, dat=data_content)

    @classmethod
    def _from_cff(cls, cf: ComtradeFile) -> "Comtrade|None":
        """从 CFF 单文件加载 Comtrade 对象"""
        cff_file = CffFile.from_file(cf.cff_path.path)
        configure = cff_file.to_configure()
        if configure is None:
            return None
        eg = cff_file.to_information()
        data_content = cff_file.to_data_content(configure)
        return cls._create_comtrade(file=cf, cfg=configure, eg=eg, dat=data_content)

    @export_format
    def save_comtrade(self, output_file_path: ComtradeFile | Path | str, **kwargs):
        """
        将 comtrade 对象保存为文件

        参数:
            output_file_path: 保存路径
            format: 导出格式 (multi_file/cff/json/csv), 默认multi_file
            data_format: dat文件格式 (ASCII/BINARY/BINARY32/FLOAT32), 默认BINARY
            **kwargs: 其他参数
        """
        pass
