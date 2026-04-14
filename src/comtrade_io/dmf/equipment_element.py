#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMF设备部件基类模块

定义DMF设备部件的基类，提供从XML元素解析设备通用属性的功能。
"""
from typing import List, Set
from xml.etree.ElementTree import Element

from comtrade_io.channel.analog import Analog
from comtrade_io.channel.status import Status
from comtrade_io.equipment.equipment import Equipment
from comtrade_io.utils import parse_int


def _find_all_elements(element: Element, ns: dict, tag_name: str) -> List[Element]:
    """
    尝试多种方式查找子元素

    参数:
        element: 父XML元素
        ns: 命名空间映射
        tag_name: 标签名

    返回:
        找到的元素列表
    """
    elems = []
    # 尝试多种方式查找元素
    if 'scl' in ns:
        elems = element.findall(f'scl:{tag_name}', ns)
    if not elems and 'ns' in ns:
        elems = element.findall(f'ns:{tag_name}', ns)
    if not elems:
        # 尝试不带前缀
        elems = element.findall(tag_name)
    if not elems:
        # 尝试使用命名空间URI直接查找
        for prefix, uri in ns.items():
            if uri:
                elems = element.findall(f'{{{uri}}}{tag_name}')
                if elems:
                    break
    return elems


def _extract_analog_indices(element: Element, ns: dict) -> Set[int]:
    """
    从元素的所有子元素中提取模拟通道索引

    会从以下元素/属性中提取：
    - AnaChn/@idx_cfg
    - ACVChn/@ua_idx, @ub_idx, @uc_idx, @un_idx, @ul_idx
    - ACC_Bran/@ia_idx, @ib_idx, @ic_idx, @in_idx
    - ACI_Bran/@ia_idx, @ib_idx, @ic_idx, @in_idx
    - SDL_RelatedAnalog/@a1, @a2, @a3, @a4
    - 也会递归搜索子元素（如 TransformerWinding）
    """
    indices = set()

    # 1. 从当前元素的直接子元素提取
    # 从 AnaChn 元素提取
    ana_elems = _find_all_elements(element, ns, 'AnaChn')
    for chn in ana_elems:
        idx_cfg = chn.get('idx_cfg')
        if idx_cfg:
            idx = parse_int(idx_cfg)
            if idx > 0:
                indices.add(idx)

    # 从 ACVChn 元素提取
    acv_elems = _find_all_elements(element, ns, 'ACVChn')
    for chn in acv_elems:
        for attr in ['ua_idx', 'ub_idx', 'uc_idx', 'un_idx', 'ul_idx']:
            val = chn.get(attr)
            if val:
                idx = parse_int(val)
                if idx > 0:
                    indices.add(idx)

    # 从 ACC_Bran 元素提取
    acc_elems = _find_all_elements(element, ns, 'ACC_Bran')
    for chn in acc_elems:
        for attr in ['ia_idx', 'ib_idx', 'ic_idx', 'in_idx']:
            val = chn.get(attr)
            if val:
                idx = parse_int(val)
                if idx > 0:
                    indices.add(idx)

    # 从 ACI_Bran 元素提取
    aci_elems = _find_all_elements(element, ns, 'ACI_Bran')
    for chn in aci_elems:
        for attr in ['ia_idx', 'ib_idx', 'ic_idx', 'in_idx']:
            val = chn.get(attr)
            if val:
                idx = parse_int(val)
                if idx > 0:
                    indices.add(idx)

    # 从 SDL_RelatedAnalog 元素提取
    related_elems = _find_all_elements(element, ns, 'SDL_RelatedAnalog')
    for chn in related_elems:
        for attr in ['a1', 'a2', 'a3', 'a4']:
            val = chn.get(attr)
            if val:
                idx = parse_int(val)
                if idx > 0:
                    indices.add(idx)

    # 2. 递归搜索所有子元素（如 TransformerWinding）
    for child in element:
        # 跳过那些我们已经检查过的特定元素
        child_tag = child.tag
        if '}' in child_tag:
            child_tag = child_tag.split('}')[-1]

        # 递归提取子元素中的通道索引
        child_indices = _extract_analog_indices(child, ns)
        indices.update(child_indices)

    return indices


def _extract_status_indices(element: Element, ns: dict) -> Set[int]:
    """
    从元素的所有子元素中提取状态通道索引

    会从以下元素/属性中提取：
    - StaChn/@idx_cfg
    - SDL_Breaker/@breaker_a, @breaker_b, @breaker_c, @breaker_a2, @breaker_b2, @breaker_c2
    - SDL_Protect/@a_trip1, @a_trip2, @b_trip1, @b_trip2, @c_trip1, @c_trip2, @reclose1, ...
    - SDL_OtherDigital/@d1, @d2, @d3, @d4
    - 也会递归搜索子元素
    """
    indices = set()

    # 1. 从当前元素的直接子元素提取
    # 从 StaChn 元素提取
    sta_elems = _find_all_elements(element, ns, 'StaChn')
    for chn in sta_elems:
        idx_cfg = chn.get('idx_cfg')
        if idx_cfg:
            idx = parse_int(idx_cfg)
            if idx > 0:
                indices.add(idx)

    # 从 SDL_Breaker 元素提取
    breaker_elems = _find_all_elements(element, ns, 'SDL_Breaker')
    for chn in breaker_elems:
        for attr in ['breaker_a', 'breaker_b', 'breaker_c',
                     'breaker_a2', 'breaker_b2', 'breaker_c2']:
            val = chn.get(attr)
            if val:
                idx = parse_int(val)
                if idx > 0:
                    indices.add(idx)

    # 从 SDL_Protect 元素提取
    protect_elems = _find_all_elements(element, ns, 'SDL_Protect')
    for chn in protect_elems:
        # 检查所有可能的属性
        for attr in chn.keys():
            if attr.startswith(('a_trip', 'b_trip', 'c_trip', 'reclose')):
                val = chn.get(attr)
                if val:
                    idx = parse_int(val)
                    if idx > 0:
                        indices.add(idx)

    # 从 SDL_OtherDigital 元素提取
    other_elems = _find_all_elements(element, ns, 'SDL_OtherDigital')
    for chn in other_elems:
        for attr in ['d1', 'd2', 'd3', 'd4']:
            val = chn.get(attr)
            if val:
                idx = parse_int(val)
                if idx > 0:
                    indices.add(idx)

    # 2. 递归搜索所有子元素
    for child in element:
        # 递归提取子元素中的通道索引
        child_indices = _extract_status_indices(child, ns)
        indices.update(child_indices)

    return indices


def parse_ans_from_xml(element: Element, ns: dict, analog_channels: dict = None,
                       use_scl_prefix: bool = True) -> List[Analog]:
    """
    从XML元素解析模拟通道列表

    参数:
        element: XML元素
        ns: 命名空间映射
        analog_channels: 模拟通道字典，根据idx_cfg查找对应的Analog对象
        use_scl_prefix: 是否使用scl命名空间前缀（保留参数兼容性）

    返回:
        Analog对象列表
    """
    if not analog_channels:
        return []

    indices = _extract_analog_indices(element, ns)

    # 按索引排序返回
    result = []
    for idx in sorted(indices):
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
        use_scl_prefix: 是否使用scl命名空间前缀（保留参数兼容性）

    返回:
        Status对象列表
    """
    if not status_channels:
        return []

    indices = _extract_status_indices(element, ns)

    # 按索引排序返回
    result = []
    for idx in sorted(indices):
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

        # 解析通道
        anas = parse_ans_from_xml(element, ns, analog_channels)
        stas = parse_sts_from_xml(element, ns, status_channels)

        return Equipment(
                index=index,
                name=name,
                reference=reference,
                uuid=uuid,
                anas=anas,
                stas=stas
        )
