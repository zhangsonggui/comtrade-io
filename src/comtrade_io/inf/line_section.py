#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel, Field

from comtrade_io.dmf import Capacitance, Impedance, MutualInductance

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


class LineSection(BaseModel):
    """线路部件模型"""
    area: str = "private"
    index: int = Field(default=0, description="线路编号")
    name: str = Field(default="线路名称", description="线路名称")
    line_length: float = Field(default=0.0, description="线路长度")
    impedance: Impedance = Field(default_factory=Impedance, description="线路阻抗")
    capacitance: Capacitance = Field(default_factory=Capacitance, description="线路电容")
    mutual_inductance: MutualInductance = Field(default_factory=MutualInductance, description="线路互感")
    voltage_indexes: list[int] = Field(default_factory=list, description="电压通道索引")
    current_indexes: list[int] = Field(default_factory=list, description="电流通道索引")
    status_indexes: list[int] = Field(default_factory=list, description="开关量通道索引")

    def from_str(self, content: str):
        pass

    @classmethod
    def from_dict(cls, data: dict):
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
        line_length = parse_number_with_unit(length_str)

        # 解析阻抗参数 RX: r1, x1, r0, x0
        rx_str = data.get('RX', '0, 0, 0, 0')
        rx_values = parse_four_values(rx_str)
        impedance = Impedance(
            r1=rx_values[0] if len(rx_values) > 0 else 0.0,
            x1=rx_values[1] if len(rx_values) > 1 else 0.0,
            r0=rx_values[2] if len(rx_values) > 2 else 0.0,
            x0=rx_values[3] if len(rx_values) > 3 else 0.0
        )

        # 解析电容参数 CG: c1, g1, c0, g0
        cg_str = data.get('CG', '0, 0, 0, 0')
        cg_values = parse_four_values(cg_str)
        capacitance = Capacitance(
            c1=cg_values[0] if len(cg_values) > 0 else 0.0,
            g1=cg_values[1] if len(cg_values) > 1 else 0.0,
            c0=cg_values[2] if len(cg_values) > 2 else 0.0,
            g0=cg_values[3] if len(cg_values) > 3 else 0.0
        )

        # 解析互感参数 MRX: mr0, mx0
        mrx_str = data.get('MRX', '0, 0')
        mrx_values = parse_two_values(mrx_str)
        mutual_inductance = MutualInductance(
            idx=int(data.get('index', 0)),
            mr0=mrx_values[0] if len(mrx_values) > 0 else 0.0,
            mx0=mrx_values[1] if len(mrx_values) > 1 else 0.0
        )

        # 解析通道索引
        def parse_indexes(s: str) -> list[int]:
            return [int(i.strip()) for i in s.split(',') if i.strip()]

        voltage_indexes = parse_indexes(data.get('TV_CHNS', ''))
        current_indexes = parse_indexes(data.get('TA_CHNS', ''))
        status_indexes = parse_indexes(data.get('STATUS_CHNS', ''))

        _line_section = {
            'area'             : data.get('area'),
            'index'            : int(data.get('index', 0)),
            'name'             : data.get('DEV_ID'),
            'line_length'      : line_length,
            'impedance'        : impedance,
            'capacitance'      : capacitance,
            'mutual_inductance': mutual_inductance,
            'voltage_indexes'  : voltage_indexes,
            'current_indexes'  : current_indexes,
            'status_indexes'   : status_indexes
        }
        return cls(**_line_section)
