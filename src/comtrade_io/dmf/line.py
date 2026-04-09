#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线路模型模块

定义线路类，用于表示电力系统中的输电线路模型。
线路是连接两个母线的电力输送通道，包含电气参数和电流分支信息。
"""
from typing import List
from xml.etree.ElementTree import Element

from pydantic import Field

from comtrade_io.dmf import Bus
from comtrade_io.dmf.branch import ACCBranch
from comtrade_io.dmf.dmf_base_model import DmfBaseModel
from comtrade_io.dmf.line_param import Capacitance, Impedance, MutualInductance
from comtrade_io.inf.line_section import LineSection
from comtrade_io.type import LineBranchNum
from comtrade_io.utils import parse_float, parse_int


class Line(DmfBaseModel):
    """
    线路类
    
    表示电力系统中的输电线路模型，包含线路的电气参数、额定值和电流分支信息。
    线路连接两个母线，用于传输电力，是电力系统分析的基本元素之一。
    
    属性:
        bus_index: 母线索引号，表示线路首端连接的母线
        v_rtg: 一次额定电压，单位通常为kV
        a_rtg: 一次额定电流，单位通常为A
        a_rtg_snd: 二次额定电流，用于保护装置的额定电流，单位通常为A
        lin_len: 线路长度，单位通常为km
        bran_num: 线路分段数，表示线路被分割成的段数，用于分布参数模型
        rx: 线路阻抗参数，包含正序和零序的电阻和电抗
        cg: 线路电容参数，包含正序和零序的电容和电导
        mr: 线路互感参数，用于表示与其他线路的互感关系
        currents: 交流电流通道列表，包含线路各段的电流分支信息
        anas: 模拟通道列表，继承自基类
        stas: 开关量通道列表，继承自基类
    """
    bus_index: int = Field(..., description="母线索引号")
    rated_primary_voltage: float = Field(default=220.0, description="一次额定电压")
    rated_primary_current: float = Field(default=1.0, description="一次额定电流")
    rated_secondary_current: float = Field(default=1.0, description="二次额定电流")
    line_length: float = Field(default=0.0, description="线路长度")
    bran_num: LineBranchNum = Field(default=LineBranchNum.B1, description="线路分段数")
    impedance: Impedance = Field(default_factory=Impedance, description="线路阻抗")
    capacitance: Capacitance = Field(default_factory=Capacitance, description="线路电容")
    mutual_inductance: MutualInductance = Field(default_factory=MutualInductance, description="线路互感")
    currents: List[ACCBranch] = Field(default_factory=list, description="交流电流通道")
    buses: List[Bus] = Field(default_factory=list, description="关联的母线列表")

    def __str__(self):
        """
        返回线路的XML字符串表示形式
        
        返回:
            格式化的XML字符串，包含线路及其所有子元素的完整表示
        """
        attrs = [
            f'idx="{self.index}"',
            f'line_name="{self.name}"',
            f'bus_ID="{self.bus_index}"',
            f'srcRef="{self.reference}"',
            f'VRtg="{self.rated_primary_voltage}"',
            f'ARtg="{self.rated_primary_current}"',
            f'ARtgSnd="{self.rated_secondary_current}"',
            f'LinLen="{self.line_length}"',
            f'bran_num="{self.bran_num.value}"',
            f'line_uuid="{self.uuid}"'
        ]
        attrs = [attr for attr in attrs if attr is not None]
        xml = f"\t<scl:Line {' '.join(attrs)} />"
        xml += "\n\t\t" + str(self.impedance)
        xml += "\n\t\t" + str(self.capacitance)
        xml += "\n\t\t" + str(self.mutual_inductance)
        for acc_branch in self.currents:
            xml += "\n\t\t" + str(acc_branch)
        xml += self._get_ana_chn_xml()
        xml += self._get_sta_chn_xml()
        xml += "\n\t</scl:Line>"
        return xml

    @classmethod
    def from_xml(cls, element: Element, ns: dict, analog_channels: dict = None, status_channels: dict = None) -> 'Line':
        """
        从XML元素中解析线路模型

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典（可选），用于解析模拟通道对象
            status_channels: 开关量通道字典（可选），用于解析开关量通道对象
            
        返回:
            Line: 线路实例
        """
        line_bran_num = element.get('bran_num', 1)
        idx = parse_int(element.get('idx', 1))
        line_name = element.get('line_name', "")
        bus_id = parse_int(element.get('bus_ID', 0))
        src_ref = element.get('srcRef', "")
        v_rtg = parse_float(element.get('VRtg', 0.0))
        a_rtg = parse_float(element.get('ARtg', 0.0))
        a_rtg_snd = parse_float(element.get('ARtgSnd', 0.0))
        line_len = parse_float(element.get('LinLen', 0.0))
        bran_num = LineBranchNum.from_value(line_bran_num, default=LineBranchNum.B1)
        line_uuid = element.get('line_uuid', "")

        line = cls(
            index=idx,
            name=line_name,
            bus_index=bus_id,
            reference=src_ref,
            rated_primary_voltage=v_rtg,
            rated_primary_current=a_rtg,
            rated_secondary_current=a_rtg_snd,
            line_length=line_len,
            bran_num=bran_num,
            uuid=line_uuid
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

        # 解析分支和通道（支持带/不带命名空间）
        if 'scl' in ns:
            acc_elems = element.findall('scl:ACC_Bran', ns)
            line.anas = cls.parse_ans_from_xml(element, ns, analog_channels=analog_channels, use_scl_prefix=True)
            line.stas = cls.parse_sts_from_xml(element, ns, status_channels=status_channels, use_scl_prefix=True)
        else:
            acc_elems = element.findall('ACC_Bran')
            line.anas = cls.parse_ans_from_xml(element, ns, analog_channels=analog_channels, use_scl_prefix=False)
            line.stas = cls.parse_sts_from_xml(element, ns, status_channels=status_channels, use_scl_prefix=False)

        # 解析ACC_Bran
        line.currents = [
            ACCBranch.from_xml(acc_elem, ns, analog_channels=analog_channels)
            for acc_elem in acc_elems
        ]

        return line

    @classmethod
    def from_line_section(cls, line_section: LineSection, analog_channels: dict = None, status_channels: dict = None):
        index = line_section.index
        name = line_section.name
        rated_primary_voltage = 220.0
        line_length = line_section.line_length
        anas = [analog_channels.get(ci) for ci in line_section.current_indexes if
                ci is not None and analog_channels.get(ci) is not None]
        stas = [status_channels.get(ci) for ci in line_section.status_indexes if
                ci is not None and status_channels.get(ci) is not None]
        line_obj = cls(index=index,
                       name=name,
                       bus_index=0,
                       rated_primary_voltage=rated_primary_voltage,
                       line_length=line_length,
                       impedance=line_section.impedance,
                       capacitance=line_section.capacitance,
                       mutual_inductance=line_section.mutual_inductance,
                       anas=anas,
                       stas=stas)
        bran_num, currents = line_obj.handle_current_branches()
        line_obj.bran_num = bran_num
        line_obj.currents = currents
        return line_obj
