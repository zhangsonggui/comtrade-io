#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMF基础模型模块

定义DMF数据模型的基础类，包括DmfBaseModelModel和ComtradeBaseModel。
这些类是所有DMF模型对象的基类，提供通用的属性和方法。
"""
from typing import List, Optional
from xml.etree.ElementTree import Element

from pydantic import Field

from comtrade_io.base import IndexBaseModel, ReferenceBaseModel
from comtrade_io.channel.analog import Analog
from comtrade_io.channel.status import Status
from comtrade_io.equipment.branch import ACCBranch
from comtrade_io.type import CurrentBranchNum
from comtrade_io.utils import parse_float


class DmfBaseModel(IndexBaseModel, ReferenceBaseModel):
    """
    数据模型基础类

    所有DMF数据模型对象的基类，提供设备通用属性的定义。
    继承自IndexBaseModel和ReferenceBaseModel，提供索引和引用功能。

    属性:
        name: 设备名称，用于标识设备
        uuid: 设备唯一标识符，用于全局唯一标识设备
        anas: 模拟通道列表，根据XML中的idx_cfg在analog_channels中查找对应的AnalogChannel对象
        stas: 开关量通道列表，根据XML中的idx_cfg在status_channels中查找对应的StatusChannel对象
    """
    name: str = Field(..., description="设备名称")
    uuid: Optional[str] = Field(default="", description="设备标识")
    anas: List[Analog] = Field(default_factory=list, description="模拟通道列表")
    stas: List[Status] = Field(default_factory=list, description="开关量通道列表")

    def handle_current_branches(self):
        """
        处理电流分支问题
        """
        if len(self.anas) <= 4:
            return CurrentBranchNum.B1, [ACCBranch.from_analog_channels(self.anas)]
        mid = len(self.anas) // 2
        b1 = ACCBranch.from_analog_channels(self.anas[:mid])
        b2 = ACCBranch.from_analog_channels(self.anas[mid:])
        return CurrentBranchNum.B2, [b1, b2]

    def __eq__(self, other):
        return self.index == other.index and self.name == other.name

    def update(self, other):
        """
        从另一个对象更新属性

        参数:
            other: 源对象，其非默认值将用于更新当前对象

        注意:
            - index和name作为标识字段不会被更新
            - 只有当other的属性与当前对象不同时才更新
        """
        if self.index != other.index or self.name != other.name:
            raise ValueError(
                f"无法更新Bus对象：标识字段不匹配 "
                f"(当前: idx={self.index}, name={self.name}; "
                f"其他: idx={other.index}, name={other.name})"
            )
        for field_name in ['rated_primary_voltage', 'rated_secondary_voltage',
                           'tv_install_site', 'voltage']:
            other_value = getattr(other, field_name)
            if getattr(self, field_name) != other_value:
                setattr(self, field_name, other_value)


class DmfRootModel(ReferenceBaseModel):
    """
    COMTRADE数据模型XML基础类

    定义XML文档的基础属性，包括命名空间、版本信息等。
    用于序列化和反序列化COMTRADE数据模型的XML表示。

    属性:
        xmlns_scl: XML命名空间（SCL命名空间）
        xmlns_xsi: XML实例命名空间
        station_name: 站点名称，表示变电站或电厂的名称
        version: 数据模型版本号
        rec_dev_name: 录波设备名称
        xsi_schema_location: XML架构文件位置
    """
    xmlns_scl: str = Field(default="http://www.iec.ch/61850/2003/SCL", description="XML命名空间")
    xmlns_xsi: str = Field(default="http://www.w3.org/2001/XMLSchema-instance", description="XML命名空间")
    station_name: str = Field(default="", description="站点名称")
    version: float = Field(default=1.0, description="数据模型版本")
    rec_dev_name: str = Field(default="", description="录波设备")
    xsi_schema_location: str = Field(default="http://www.iec.ch/61850/2003/SCLcomtrade_mdl_v1.1.xsd",
                                     description="XML架构")

    def __str__(self):
        """
        返回COMTRADE模型XML根元素的字符串表示

        返回:
            格式化的XML字符串，包含XML声明和根元素开始标签
        """
        attrs = [
            f'xmlns:scl="{self.xmlns_scl}"',
            f'xmlns:xsi="{self.xmlns_xsi}"',
            f'stationName="{self.station_name}"',
            f'version="{self.version}"',
            f'recDevName="{self.rec_dev_name}"',
            f'xsi:schemaLocation="{self.xsi_schema_location}"'
        ]
        xml = f'<?xml version="1.0" encoding="UTF-8"?>'
        xml += "\n" + f'<scl:ComtradeModel {",".join(attrs)}>'
        return xml

    @classmethod
    def from_xml(cls, element: Element, ns: dict) -> 'DmfRootModel':
        """
        从XML元素创建ComtradeBaseModel实例

        参数:
            element: XML元素
            ns: 命名空间

        返回:
            ComtradeBaseModel实例
        """
        return cls(
            station_name=element.get('station_name', ''),
            version=parse_float(element.get('version', '1.0')),
            rec_dev_name=element.get('rec_dev_name', ''),
            xmlns_scl=element.get('xmlns:scl', 'http://www.iec.ch/61850/2003/SCL'),
            xmlns_xsi=element.get('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance'),
            xsi_schema_location=element.get('xsi:schemaLocation',
                                            'http://www.iec.ch/61850/2003/SCLcomtrade_mdl_v1.1.xsd')
        )
