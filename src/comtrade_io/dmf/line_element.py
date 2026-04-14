#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线路部件处理模块

定义线路部件类，用于从XML元素解析线路模型。
"""
from xml.etree.ElementTree import Element

from comtrade_io.dmf.equipment_element import EquipmentElement
from comtrade_io.equipment import Line
from comtrade_io.equipment.branch import ACCBranch
from comtrade_io.equipment.line_param import Capacitance, Impedance, MutualInductance
from comtrade_io.type import CurrentBranchNum
from comtrade_io.utils import parse_float, parse_int


class LineElement(EquipmentElement):
    """线路部件处理"""

    @classmethod
    def from_xml(cls,
                 element: Element,
                 ns: dict,
                 analog_channels: dict = None,
                 status_channels: dict = None) -> Line:
        """
        从XML元素解析线路模型

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典
            status_channels: 开关量通道字典

        返回:
            Line: 线路实例
        """
        base = super().from_xml(element, ns, analog_channels, status_channels)

        # 解析线路特定属性
        line_bran_num = element.get('bran_num', 1)
        bus_id = parse_int(element.get('bus_ID', 0))
        v_rtg = parse_float(element.get('VRtg', 0.0))
        a_rtg = parse_float(element.get('ARtg', 0.0))
        a_rtg_snd = parse_float(element.get('ARtgSnd', 0.0))
        line_len = parse_float(element.get('LinLen', 0.0))
        bran_num = CurrentBranchNum.from_value(line_bran_num, default=CurrentBranchNum.B1)

        line = Line(
                index=base.index,
                name=base.name,
                reference=base.reference,
                uuid=base.uuid,
                anas=base.anas,
                stas=base.stas,
                bus_index=bus_id,
                rated_primary_voltage=v_rtg,
                rated_primary_current=a_rtg,
                rated_secondary_current=a_rtg_snd,
                line_length=line_len,
                current_bran_num=bran_num
        )

        # 解析线路参数（支持带/不带命名空间）
        rx_elem = element.find('scl:RX', ns) if 'scl' in ns else element.find('RX')
        if rx_elem is not None:
            line.impedance = Impedance(
                    r1=parse_float(rx_elem.get('r1', 0.0)),
                    x1=parse_float(rx_elem.get('x1', 0.0)),
                    r0=parse_float(rx_elem.get('r0', 0.0)),
                    x0=parse_float(rx_elem.get('x0', 0.0))
            )

        cg_elem = element.find('scl:CG', ns) if 'scl' in ns else element.find('CG')
        if cg_elem is not None:
            line.capacitance = Capacitance(
                    c0=parse_float(cg_elem.get('c0', 0.0)),
                    c1=parse_float(cg_elem.get('c1', 0.0)),
                    g0=parse_float(cg_elem.get('g0', 0.0)),
                    g1=parse_float(cg_elem.get('g1', 0.0))
            )

        mr_elem = element.find('scl:MR', ns) if 'scl' in ns else element.find('MR')
        if mr_elem is not None:
            line.mutual_inductance = MutualInductance(
                    idx=parse_int(mr_elem.get('idx', 0)),
                    mr0=parse_float(mr_elem.get('mr0', 0.0)),
                    mx0=parse_float(mr_elem.get('mx0', 0.0))
            )

        # 解析ACC_Bran元素
        if 'scl' in ns:
            acc_elems = element.findall('scl:ACC_Bran', ns)
        else:
            acc_elems = element.findall('ACC_Bran')

        line.currents = [
            ACCBranch.from_xml(acc_elem, ns, analog_channels=analog_channels)
            for acc_elem in acc_elems
        ]

        return line
