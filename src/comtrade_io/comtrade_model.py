#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import Optional

from pydantic import BaseModel, Field, model_serializer

from comtrade_io.base.description import Description
from comtrade_io.channel import Analog, Status
from comtrade_io.equipment import Bus, Line, Transformer


class ComtradeModel(BaseModel):
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
    analogs: Optional[dict[int, Analog]] = Field(default_factory=dict, description="模拟通道")
    statuses: Optional[dict[int, Status]] = Field(default_factory=dict, description="状态量通道")

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

    def to_dmf(self) -> str:
        """将 ComtradeModel 对象转换为DMF格式XML字符串

        返回:
            str: 转换后的DMF格式XML字符串
        """
        pass

    def to_inf(self) -> str:
        """将 ComtradeModel 模型转换为部件模型

        返回:
            str: 部件模型字符串
        """
        pass

    def write_dmf(self, path: str) -> None:
        """将 ComtradeModel 模型写入DMF文件

        参数:
            path: DMF文件路径

        异常:
            IOError: 当文件写入失败时抛出
        """
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_dmf())
        logging.info(f"DMF文件{path}写入成功")

    def write_inf(self, path: str) -> None:
        """将 ComtradeModel 模型写入部件模型文件

        参数:
            path: 部件模型文件路径

        异常:
            IOError: 当文件写入失败时抛出
        """
        with open(path, 'w', encoding='gbk') as f:
            f.write(self.to_inf())
        logging.info(f"INF文件{path}写入成功")
