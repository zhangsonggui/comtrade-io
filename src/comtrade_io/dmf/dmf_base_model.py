#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMF基础模型模块

定义DMF数据模型的基础类，包括DmfBaseModelModel和ComtradeBaseModel。
这些类是所有DMF模型对象的基类，提供通用的属性和方法。
"""
from typing import List, Optional
from xml.etree.ElementTree import Element

from comtrade_io.base import IndexBaseModel, ReferenceBaseModel
from comtrade_io.dmf.analog_channel import AnalogChannel
from comtrade_io.dmf.status_channel import StatusChannel
from comtrade_io.utils import parse_float, parse_int
from pydantic import Field


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
    anas: List[AnalogChannel] = Field(default_factory=list, description="模拟通道列表")
    stas: List[StatusChannel] = Field(default_factory=list, description="开关量通道列表")

    def get_ana_chn_xml(self) -> str:
        """
        获取模拟通道的XML字符串表示
        
        返回:
            格式化的XML字符串，包含所有模拟通道元素
        """
        xml = ""
        for ana_chn in self.anas:
            if ana_chn is not None:
                xml += "\n\t\t" + f'<scl:AnaChn idx_cfg="{ana_chn.index}" />'
        return xml

    def get_sta_chn_xml(self) -> str:
        """
        获取开关量通道的XML字符串表示
        
        返回:
            格式化的XML字符串，包含所有开关量通道元素
        """
        xml = ""
        for sta_chn in self.stas:
            if sta_chn is not None:
                xml += "\n\t\t" + f'<scl:StaChn idx_cfg="{sta_chn.index}" />'
        return xml

    @classmethod
    def parse_ans_from_xml(cls, element: Element, ns: dict, analog_channels: dict = None, use_scl_prefix: bool = True) -> List[AnalogChannel]:
        """
        从XML元素解析模拟通道列表
        
        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典，根据idx_cfg查找对应的AnalogChannel对象
            use_scl_prefix: 是否使用scl命名空间前缀
            
        返回:
            AnalogChannel对象列表
        """
        if use_scl_prefix and 'scl' in ns:
            ana_elems = element.findall('scl:AnaChn', ns)
        else:
            ana_elems = element.findall('AnaChn')
        
        result = []
        for chn in ana_elems:
            idx_cfg = chn.get('idx_cfg')
            if idx_cfg and analog_channels:
                idx = parse_int(idx_cfg)
                if idx in analog_channels:
                    result.append(analog_channels[idx])
        return result

    @classmethod
    def parse_sts_from_xml(cls, element: Element, ns: dict, status_channels: dict = None, use_scl_prefix: bool = True) -> List[StatusChannel]:
        """
        从XML元素解析开关量通道列表
        
        参数:
            element: XML元素
            ns: 命名空间映射
            status_channels: 开关量通道字典，根据idx_cfg查找对应的StatusChannel对象
            use_scl_prefix: 是否使用scl命名空间前缀
            
        返回:
            StatusChannel对象列表
        """
        if use_scl_prefix and 'scl' in ns:
            sta_elems = element.findall('scl:StaChn', ns)
        else:
            sta_elems = element.findall('StaChn')
        
        result = []
        for chn in sta_elems:
            idx_cfg = chn.get('idx_cfg')
            if idx_cfg and status_channels:
                idx = parse_int(idx_cfg)
                if idx in status_channels:
                    result.append(status_channels[idx])
        return result


class ComtradeBaseModel(ReferenceBaseModel):
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
    def from_xml(cls, element: Element, ns: dict) -> 'ComtradeBaseModel':
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
