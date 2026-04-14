#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
开关量通道模块

定义开关量通道类，继承自Digital和DmfChannel，用于表示电力系统中的开关量测量通道。
开关量通道用于采集断路器、隔离开关等设备的分合状态。
"""
from xml.etree.ElementTree import Element

from comtrade_io.channel.status import Status
from comtrade_io.type import Contact, DigitalChannelFlag, DigitalChannelType
from comtrade_io.utils import get_logger, parse_int

logging = get_logger()


class StatusElement:
    """
    开关量通道类
    
    表示电力系统中的开关量通道，用于采集断路器、隔离开关、保护装置等设备
    的分合状态和告警信息。继承自Digital和DmfChannel。
    
    属性:
        reference: IEC61850参引，用于关联到IEC61850数据模型中的相应数据对象
        data: 通道数据，一维数组
    """

    @classmethod
    def from_xml(cls, element: Element) -> Status:
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

        return Status(
                index=parse_int(element.get('idx_cfg', 1)),
                idx_org=parse_int(element.get('idx_org', 1)),
                type=_type,
                flag=_flag,
                contact=Contact.from_name(_contact),
                reference=element.get('srcRef', '')
        )
