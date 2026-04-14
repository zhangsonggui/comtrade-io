#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
变压器部件处理模块

定义变压器部件类，用于从XML元素解析变压器模型。
"""
from xml.etree.ElementTree import Element

from comtrade_io.dmf.equipment_element import EquipmentElement
from comtrade_io.equipment.branch import ACCBranch, ACVBranch
from comtrade_io.equipment.transformer import Transformer, TransformerWinding
from comtrade_io.equipment.transformer_winding import Igap, WindGroup
from comtrade_io.type import CurrentBranchNum, TransWindLocation, WindFlag
from comtrade_io.utils import parse_float, parse_int


class TransformerWindingSection:
    """变压器绕组部件处理"""

    @classmethod
    def from_xml(cls, element: Element, ns: dict, analog_channels: dict = None) -> TransformerWinding:
        """
        从XML元素解析变压器绕组

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典

        返回:
            TransformerWinding: 变压器绕组实例
        """
        location = TransWindLocation.from_value(element.get('location', ""),
                                                default=TransWindLocation.HIGH)
        src_ref = element.get('srcRef', "")
        v_rtg = parse_float(element.get('VRtg', 0.0))
        a_rtg = parse_float(element.get('ARtg', 0.0))
        bran_num = parse_int(element.get('bran_num', 0))
        bran_num = CurrentBranchNum.from_value(bran_num, default=CurrentBranchNum.B1)

        # 查找 WG 元素（支持带/不带命名空间）
        wg_elem = element.find('scl:wG', ns) if 'scl' in ns else element.find('wG')
        wg = WindGroup(
                angle=parse_int(wg_elem.get('angle', 0)) if wg_elem else 0,
                wind_flag=WindFlag.from_value(wg_elem.get('wgroup', "") if wg_elem else "", default=WindFlag.Y)
        )
        bus_id = parse_int(element.get('bus_ID', 0))

        tfw = TransformerWinding(
                trans_wind_location=location,
                reference=src_ref,
                rated_voltage=v_rtg,
                rated_current=a_rtg,
                bran_num=bran_num,
                wind_group=wg,
                bus_id=bus_id
        )

        # 查找 ACVChn 元素（支持带/不带命名空间）
        acv_chn_elem = element.find('scl:ACVChn', ns) if 'scl' in ns else element.find('ACVChn')
        if acv_chn_elem is not None:
            tfw.voltage = ACVBranch.from_xml(acv_chn_elem, ns, analog_channels=analog_channels)

        # 查找 ACC_Bran 元素（支持带/不带命名空间）
        if 'scl' in ns:
            acc_elems = element.findall('scl:ACC_Bran', ns)
        else:
            acc_elems = element.findall('ACC_Bran')
        tfw.currents = [
            ACCBranch.from_xml(chn, ns, analog_channels=analog_channels)
            for chn in acc_elems
        ]

        # 查找 Igap 元素（支持带/不带命名空间）
        igap_elem = element.find('scl:Igap', ns) if 'scl' in ns else element.find('Igap')
        if igap_elem is not None:
            zgap_idx_val = parse_int(igap_elem.get("zGap_idx", 0))
            zsgap_idx_val = parse_int(igap_elem.get("zSGap_idx", 0))
            zgap = analog_channels.get(zgap_idx_val, None)
            zsgap = analog_channels.get(zsgap_idx_val, None)
            tfw.igap = Igap(zgap=zgap, zsgap=zsgap)

        return tfw


class TransformerElement(EquipmentElement):
    """变压器部件处理"""

    @classmethod
    def from_xml(cls,
                 element: Element,
                 ns: dict,
                 analog_channels: dict = None,
                 status_channels: dict = None) -> Transformer:
        """
        从XML元素解析变压器模型

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典
            status_channels: 开关量通道字典

        返回:
            Transformer: 变压器实例
        """
        base = super().from_xml(element, ns, analog_channels, status_channels)

        # 解析变压器特定属性
        pwr_rtg = parse_float(element.get('pwrRtg', 0.0))

        transformer = Transformer(
                index=base.index,
                name=base.name,
                reference=base.reference,
                uuid=base.uuid,
                anas=base.anas,
                stas=base.stas,
                capacity=pwr_rtg
        )

        # 解析变压器绕组（支持带/不带命名空间）
        if 'scl' in ns:
            transformer.trans_winds = [
                TransformerWindingSection.from_xml(tw, ns, analog_channels=analog_channels)
                for tw in element.findall('scl:TransformerWinding', ns)
            ]
        else:
            transformer.trans_winds = [
                TransformerWindingSection.from_xml(tw, ns, analog_channels=analog_channels)
                for tw in element.findall('TransformerWinding')
            ]

        return transformer
