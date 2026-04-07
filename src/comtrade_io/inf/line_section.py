#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import Field

from comtrade_io.dmf.line_param import Capacitance, Impedance, MutualInductance
from comtrade_io.inf.section_base_model import SectionBaseModel

line_dict = {'CG'         : '0(μf/km), 0(S/km), 0(μf/km), 0(S/km)',
             'DEV_ID'     : '14,220kV 602大晃线第一套合并单元电流',
             'LENGTH'     : '22.45(km)', 'MRX': '0(Ω/km), 0(Ω/km)',
             'OBJECT_TYPE': 'LINE', 'REACTOR': '-1(Ω)',
             'RX'         : '0.071(Ω/km), 0.44(Ω/km), 0.351(Ω/km), 1.324(Ω/km)',
             'STATUS_CHNS': '142, 143, 144, 145, 146, 147, 148, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175',
             'SYS_ID'     : '', 'TA_CHNS': '41, 42, 43, 0, 1',
             'TV_CHNS'    : '46, 47, 48, 0',
             'area'       : 'ZYHD',
             'index'      : 1,
             'type'       : 'Line'}


class LineSection(SectionBaseModel):
    """线路部件模型"""
    line_length: float = Field(default=0.0, description="线路长度")
    impedance: Impedance = Field(default_factory=Impedance, description="线路阻抗")
    capacitance: Capacitance = Field(default_factory=Capacitance, description="线路电容")
    mutual_inductance: MutualInductance = Field(default_factory=MutualInductance, description="线路互感")
    current_indexes: list[int] = Field(default_factory=list, description="电流通道索引")

    @classmethod
    def from_dict(cls, data: dict):
        ls = super().from_dict(data)

        def parse_number_with_unit(s: str) -> float:
            match = re.search(r'\d+\.?\d*', s)
            return float(match.group()) if match else 0.0

        def parse_four_values(s: str) -> list[float]:
            parts = s.split(',')
            return [parse_number_with_unit(p) for p in parts[:4]]

        def parse_two_values(s: str) -> list[float]:
            parts = s.split(',')
            return [parse_number_with_unit(p) for p in parts[:2]]

        # 解析线路长度
        length_str = data.get('LENGTH', '0(km)')
        ls.line_length = parse_number_with_unit(length_str)

        # 解析阻抗参数 RX: r1, x1, r0, x0
        rx_str = data.get('RX', '0, 0, 0, 0')
        rx_values = parse_four_values(rx_str)
        ls.impedance = Impedance(
            r1=rx_values[0] if len(rx_values) > 0 else 0.0,
            x1=rx_values[1] if len(rx_values) > 1 else 0.0,
            r0=rx_values[2] if len(rx_values) > 2 else 0.0,
            x0=rx_values[3] if len(rx_values) > 3 else 0.0
        )

        # 解析电容参数 CG: c1, g1, c0, g0
        cg_str = data.get('CG', '0, 0, 0, 0')
        cg_values = parse_four_values(cg_str)
        ls.capacitance = Capacitance(
            c1=cg_values[0] if len(cg_values) > 0 else 0.0,
            g1=cg_values[1] if len(cg_values) > 1 else 0.0,
            c0=cg_values[2] if len(cg_values) > 2 else 0.0,
            g0=cg_values[3] if len(cg_values) > 3 else 0.0
        )

        # 解析互感参数 MRX: mr0, mx0
        mrx_str = data.get('MRX', '0, 0')
        mrx_values = parse_two_values(mrx_str)
        ls.mutual_inductance = MutualInductance(
            idx=int(data.get('index', 0)),
            mr0=mrx_values[0] if len(mrx_values) > 0 else 0.0,
            mx0=mrx_values[1] if len(mrx_values) > 1 else 0.0
        )

        ls.current_indexes = cls.parse_indexes(data.get('TA_CHNS', ''))

        return ls
