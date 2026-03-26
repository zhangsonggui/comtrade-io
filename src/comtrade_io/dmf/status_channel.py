#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
开关量通道模块

定义开关量通道类，继承自Digital和DmfChannel，用于表示电力系统中的开关量测量通道。
开关量通道用于采集断路器、隔离开关等设备的分合状态。
"""
from typing import Any, Optional
from xml.etree.ElementTree import Element

import numpy as np
from pydantic import Field, field_serializer

from comtrade_io.cfg import Status
from comtrade_io.dmf.dmf_channel import DmfChannel
from comtrade_io.type import Contact, DigitalChannelFlag, DigitalChannelType
from comtrade_io.utils import get_logger, parse_int

logging = get_logger()


class StatusChannel(Status, DmfChannel):
    """
    开关量通道类
    
    表示电力系统中的开关量通道，用于采集断路器、隔离开关、保护装置等设备
    的分合状态和告警信息。继承自Digital和DmfChannel。
    
    属性:
        reference: IEC61850参引，用于关联到IEC61850数据模型中的相应数据对象
        data: 通道数据，一维数组
    """
    reference: str = Field(default="", description="IEC61850参引")
    data: Optional[Any] = Field(default=None, description="通道数据，一维数组")

    @field_serializer('data')
    def serialize_data(self, data: Any) -> Optional[list]:
        if data is None:
            return None
        if isinstance(data, np.ndarray):
            return data.tolist()
        return data

    def __str__(self) -> str:
        """
        返回开关量通道的XML字符串表示形式
        
        返回:
            格式化的XML字符串，表示开关量通道的所有属性
        """
        attrs = [
            f'idx_cfg="{self.index}"',
            f'idx_org="{self.idx_org}"',
            f'type="{self.type}"',
            f'flag="{self.flag}"',
            f'contact="{self.contact}"',
            f'reference="{self.reference}"'
        ]
        return f"\t<scl:StatusChannel {''.join(attrs)} />"

    @classmethod
    def from_digital(cls, digital: Status) -> "StatusChannel":
        """从Digital实例创建StatusChannel实例

        参数:
            digital (Digital): Digital实例

        返回:
            StatusChannel: StatusChannel实例
        """
        # 将Digital实例转换为字典
        digital_dict = digital.model_dump()
        # 设置必需的 idx_org 字段，默认与 index 相同
        digital_dict['idx_org'] = digital_dict.get('index', 1)
        # 使用字典创建StatusChannel实例
        return cls(**digital_dict)

    @classmethod
    def from_xml(cls, element: Element, ns: Optional[dict] = None,
                 digital: Optional[Status] = None) -> "StatusChannel":
        """从XML元素创建StatusChannel实例

        参数:
            element (Element): XML元素
            ns (dict, optional): 命名空间映射
            digital (Digital, optional): 用于对比和更新的Digital实例
            
        返回:
            StatusChannel: StatusChannel实例
        """
        _contact = element.get('contact', 'NormallyOpen')
        _type = DigitalChannelType.from_value(element.get('type', ''))
        _flag = DigitalChannelFlag.from_value(element.get('flag', ''))
        if _type != _flag.type:
            _type = _flag.type

        channel = cls(
            index=parse_int(element.get('idx_cfg', 1)),
            idx_org=parse_int(element.get('idx_org', 1)),
            type=_type,
            flag=_flag,
            contact=Contact.from_name(_contact),
            reference=element.get('srcRef', '')
        )

        if digital is not None:
            digital_dict = digital.model_dump()
            for key, value in digital_dict.items():
                if hasattr(channel, key):
                    current_value = getattr(channel, key)
                    if current_value != value:
                        setattr(channel, key, value)

        return channel
