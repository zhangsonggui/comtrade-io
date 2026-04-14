#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMF设备部件基类模块

定义DMF设备部件的基类，提供从XML元素解析设备通用属性的功能。
"""
from typing import List
from xml.etree.ElementTree import Element

from comtrade_io.channel.analog import Analog
from comtrade_io.channel.status import Status
from comtrade_io.equipment.equipment import Equipment
from comtrade_io.utils import parse_int


def parse_ans_from_xml(element: Element, ns: dict, analog_channels: dict = None,
                       use_scl_prefix: bool = True) -> List[Analog]:
    """
    从XML元素解析模拟通道列表

    参数:
        element: XML元素
        ns: 命名空间映射
        analog_channels: 模拟通道字典，根据idx_cfg查找对应的Analog对象
        use_scl_prefix: 是否使用scl命名空间前缀

    返回:
        Analog对象列表
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


def parse_sts_from_xml(element: Element, ns: dict, status_channels: dict = None,
                       use_scl_prefix: bool = True) -> List[Status]:
    """
    从XML元素解析开关量通道列表

    参数:
        element: XML元素
        ns: 命名空间映射
        status_channels: 开关量通道字典，根据idx_cfg查找对应的Status对象
        use_scl_prefix: 是否使用scl命名空间前缀

    返回:
        Status对象列表
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


class EquipmentElement:
    """DMF设备部件基类"""

    @classmethod
    def from_xml(cls,
                 element: Element,
                 ns: dict,
                 analog_channels: dict = None,
                 status_channels: dict = None) -> Equipment:
        """
        从XML元素解析设备通用属性

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典
            status_channels: 开关量通道字典

        返回:
            DmfBaseModel: 包含通用属性的基础模型实例
        """
        # 解析通用属性
        index = parse_int(element.get('idx', 1))
        name = element.get('bus_name', element.get('line_name', element.get('trm_name', '')))
        reference = element.get('srcRef', '')
        uuid = element.get('bus_uuid', element.get('line_uuid', element.get('transformer_uuid', '')))

        # 解析通道（支持带/不带命名空间）
        use_scl_prefix = 'scl' in ns
        anas = parse_ans_from_xml(element, ns, analog_channels, use_scl_prefix)
        stas = parse_sts_from_xml(element, ns, status_channels, use_scl_prefix)

        return Equipment(
                index=index,
                name=name,
                reference=reference,
                uuid=uuid,
                anas=anas,
                stas=stas
        )
