#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
母线部件处理模块

定义母线部件类，用于从XML元素解析母线模型。
"""
from xml.etree.ElementTree import Element

from comtrade_io.dmf.equipment_element import EquipmentElement
from comtrade_io.equipment import Bus
from comtrade_io.equipment.branch import ACVBranch
from comtrade_io.type import TvInstallSite
from comtrade_io.utils import parse_float


class BusElement(EquipmentElement):
    """母线部件处理"""

    @classmethod
    def from_xml(cls,
                 element: Element,
                 ns: dict,
                 analog_channels: dict = None,
                 status_channels: dict = None) -> Bus:
        """
        从XML元素解析母线模型

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典
            status_channels: 开关量通道字典

        返回:
            Bus: 母线实例
        """
        base = super().from_xml(element, ns, analog_channels, status_channels)

        # 解析母线特定属性
        v_rtg = parse_float(element.get('VRtg', 0.0))
        v_rtg_snd = parse_float(element.get('VRtgSnd', 100.0))
        v_rtg_snd_pos_str = element.get('VRtgSnd_Pos', "")
        v_rtg_snd_pos = TvInstallSite.from_value(v_rtg_snd_pos_str, default=TvInstallSite.BUS)

        bus = Bus(
                index=base.index,
                name=base.name,
                reference=base.reference,
                uuid=base.uuid,
                anas=base.anas,
                stas=base.stas,
                rated_primary_voltage=v_rtg,
                rated_secondary_voltage=v_rtg_snd,
                tv_install_site=v_rtg_snd_pos
        )

        # 查找 ACVChn 元素（支持带/不带命名空间）
        acv_chn_elem = element.find('scl:ACVChn', ns) if 'scl' in ns else None
        if acv_chn_elem is None:
            acv_chn_elem = element.find('ACVChn')
        if acv_chn_elem is not None:
            bus.voltage = ACVBranch.from_xml(acv_chn_elem, ns, analog_channels=analog_channels)

        return bus
