#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Optional

from pydantic import Field, model_serializer

from comtrade_io.base.description import Description
from comtrade_io.cfg.configure import Configure
from comtrade_io.channel import Analog, Status
from comtrade_io.equipment import Bus, EquipmentGroup, Line, Transformer


class ComtradeModel(Configure):
    """COMTRADE数据模型基类

    定义COMTRADE数据模型的核心结构，包含电力系统设备（母线、线路、变压器）
    和通道数据（模拟量、状态量）。

    属性:
        buses: 母线列表
        lines: 线路列表
        transformers: 变压器列表
        analogs: 模拟通道字典，键为通道索引
        statuses: 状态量通道字典，键为通道索引
    """
    description: Description = Field(default_factory=Description, description="描述文件")
    buses: Optional[list[Bus]] = Field(default_factory=list, description="母线")
    lines: Optional[list[Line]] = Field(default_factory=list, description="线路")
    transformers: Optional[list[Transformer]] = Field(default_factory=list, description="变压器")

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        """序列化模型时将字典转换为列表

        参数:
            handler: Pydantic序列化处理器

返回:
            dict: 序列化后的数据字典
        """
        data = handler(self)
        data['analogs'] = list(self.analogs.values())
        data['statuses'] = list(self.statuses.values())
        return data

    @classmethod
    def from_configure(cls, cfg: Configure) -> "ComtradeModel":
        """根据配置文件生成ComtradeModel对象

        使用 model_construct 避免重复验证，提升性能。

        参数:
            cfg: 配置文件对象
        """
        return cls.model_construct(
                header=cfg.header,
                channel_num=cfg.channel_num,
                analogs=cfg.analogs,
                statuses=cfg.statuses,
                sampling=cfg.sampling,
                start_time=cfg.start_time,
                fault_time=cfg.fault_time,
                data_type=cfg.data_type,
                timemult=cfg.timemult,
                time_info=cfg.time_info,
                sampling_time_quality=cfg.sampling_time_quality,
                description=Description(
                        version=cfg.header.version,
                        station_name=cfg.header.station,
                        rec_dev_name=cfg.header.recorder,
                ),
        )

    def from_equipment_group(self, eg: EquipmentGroup):
        """根据设备组生成ComtradeModel对象

        参数:
            eg (EquipmentGroup): 设备组对象

        返回:
            ComtradeModel: 生成的ComtradeModel对象
        """
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

    def generate_equipment_group(self) -> EquipmentGroup:
        """生成设备组对象

        返回:
            EquipmentGroup: 设备组对象
        """
        pass

    def get_bus_info(self, name: str) -> Bus | None:
        """根据名称获取母线信息

        参数:
            name: 母线名称

        返回:
            Bus | None: 母线对象，如果未找到则返回None
        """
        if self.buses is None:
            return None

        return next((bus for bus in self.buses if bus.name == name), None)

    def get_line_info(self, name: str) -> Line | None:
        """根据名称获取线路信息

        参数:
            name: 线路名称

        返回:
            Line | None: 线路对象，如果未找到则返回None
        """
        if self.lines is None:
            return None
        return next((line for line in self.lines if line.name == name), None)

    def get_transformer_info(self, name: str) -> Transformer | None:
        """根据名称获取变压器信息

        参数:
            name: 变压器名称

        返回:
            Transformer | None: 变压器对象，如果未找到则返回None
        """
        if self.transformers is None:
            return None
        return next((trans for trans in self.transformers if trans.name == name), None)

    def get_analog_channel_info(self, index: int) -> Optional[Analog]:
        """根据索引获取模拟量通道

        参数:
            index: 通道索引

        返回:
            Optional[Analog]: 模拟量通道，未找到返回 None
        """
        if self.analogs is None:
            return None
        return self.analogs.get(index)

    def get_status_channel_info(self, index: int) -> Optional[Status]:
        """根据索引获取开关量通道

        参数:
            index: 通道索引

        返回:
            Optional[Status]: 开关量通道，未找到返回 None
        """
        if self.statuses is None:
            return None
        return self.statuses.get(index)

    def to_cfg(self):
        """将 ComtradeModel 模型转换为CFG格式字符串

        返回:
            str: 部件模型字符串
        """
        return super().__str__()

    def to_dmf(self) -> str:
        """将 ComtradeModel 对象转换为DMF格式XML字符串

        返回:
            str: 转换后的DMF格式XML字符串
        """
        attrs = [
            f"{str(self.description)}",

        ]
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
        """将 ComtradeModel 模型转换为部件模型

        返回:
            str: 部件模型字符串
        """
        inf_str = self.description.to_inf()
        attrs = [
            f"Total_Channel_Count={self.channel_num.total}",
            f"Analog_Channel_Count={self.channel_num.analog}",
            f"Status_Channel_Count={self.channel_num.status}",
            f"Line_Frequency={self.sampling.freq}",
            f"Sample_Rate_Count={len(self.sampling)}",
        ]
        for idx, segment in enumerate(self.sampling.segments):
            attrs.append(f"Sample_Rate_#{idx + 1}={segment.samp}")
            attrs.append(f"End_Sample_Rate_#{idx + 1}={segment.end_point}")
        attrs.append(f"File_Start_Time={str(self.start_time)}")
        attrs.append(f"Trigger_Time={str(self.fault_time)}")
        attrs.append(f"File_Type={self.data_type.value}")
        attrs.append(f"Time_Multiplier={self.timemult}")

        for analog in self.analogs.values():
            attrs.append(f"\n")
            attrs.append(analog.to_inf())
        for status in self.statuses.values():
            attrs.append(f"\n")
            attrs.append(status.to_inf())

        # 模拟量通道参数段
        if self.analogs:
            attrs.append(f"\n")
            attrs.append("[ZYHD Analog_Channels_Parameter]")
            for analog in self.analogs.values():
                attrs.append(f"CHNL_INFO_#{analog.index}={analog.to_inf_parameter()}")

        # 开关量通道参数段
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
        attr_str = "\n".join(attrs)
        return inf_str + "\n" + attr_str

    def write_cfg(self, path: str) -> None:
        """将 ComtradeModel 模型写入CFG文件

        参数:
            path: CFG文件路径

        异常:
            IOError: 当文件写入失败时抛出
        """
        super().write_file(path)

    def write_dmf(self, path: str) -> None:
        """将 ComtradeModel 模型写入DMF文件

        参数:
            path: DMF文件路径

        异常:
            IOError: 当文件写入失败时抛出
        """
        with open(path, 'w', encoding='utf-8', errors='ignore') as f:
            f.write(self.to_dmf())
        logging.info(f"DMF文件{path}写入成功")

    def write_inf(self, path: str) -> None:
        """将 ComtradeModel 模型写入部件模型文件

        参数:
            path: 部件模型文件路径

        异常:
            IOError: 当文件写入失败时抛出
        """
        with open(path, 'w', encoding='gbk', errors='ignore') as f:
            f.write(self.to_inf())
        logging.info(f"INF文件{path}写入成功")
