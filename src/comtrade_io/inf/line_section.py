#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.channel import Analog, Status
from comtrade_io.equipment import Line
from comtrade_io.equipment.branch import ACCBranch
from comtrade_io.equipment.line_param import Capacitance, Impedance, MutualInductance
from comtrade_io.inf.equipment_section import EquipmentSection, parse_four_values, parse_number_with_unit, \
    parse_two_values
from comtrade_io.type import CurrentBranchNum


class LineSection(EquipmentSection):
    """线路部件处理"""

    @classmethod
    def from_dict(cls,
                  data: dict,
                  analog_channels: dict[int, Analog],
                  status_channels: dict[int, Status]) -> 'Line':
        equipment = super().from_dict(data, analog_channels, status_channels)
        line = Line(index=equipment.index,
                    uuid=equipment.uuid,
                    name=equipment.name,
                    stas=equipment.stas,
                    acvs=equipment.acvs,
                    accs=equipment.accs)

        # 解析线路长度
        length_str = data.get('LENGTH', '0(km)')
        line.line_length = parse_number_with_unit(length_str)

        # 解析阻抗参数 RX: r1, x1, r0, x0
        rx_str = data.get('RX', '0, 0, 0, 0')
        rx_values = parse_four_values(rx_str)
        line.impedance = Impedance(
                r1=rx_values[0] if len(rx_values) > 0 else 0.0,
                x1=rx_values[1] if len(rx_values) > 1 else 0.0,
                r0=rx_values[2] if len(rx_values) > 2 else 0.0,
                x0=rx_values[3] if len(rx_values) > 3 else 0.0
        )

        # 解析电容参数 CG: c1, g1, c0, g0
        cg_str = data.get('CG', '0, 0, 0, 0')
        cg_values = parse_four_values(cg_str)
        line.capacitance = Capacitance(
                c1=cg_values[0] if len(cg_values) > 0 else 0.0,
                g1=cg_values[1] if len(cg_values) > 1 else 0.0,
                c0=cg_values[2] if len(cg_values) > 2 else 0.0,
                g0=cg_values[3] if len(cg_values) > 3 else 0.0
        )

        # 解析互感参数 MRX: mr0, mx0
        mrx_str = data.get('MRX', '0, 0')
        mrx_values = parse_two_values(mrx_str)
        line.mutual_inductance = MutualInductance(
                idx=int(data.get('index', 0)),
                mr0=mrx_values[0] if len(mrx_values) > 0 else 0.0,
                mx0=mrx_values[1] if len(mrx_values) > 1 else 0.0
        )
        line.currents = ACCBranch.from_analog_channels(line.accs)
        if len(line.currents) > 1:
            line.current_bran_num = CurrentBranchNum.B2

        return line
