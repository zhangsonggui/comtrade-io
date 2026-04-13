#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import Field

from comtrade_io.equipment.branch import ACCBranch
from comtrade_io.equipment.bus import Bus
from comtrade_io.equipment.equipment import Equipment
from comtrade_io.equipment.line_param import Capacitance, Impedance, MutualInductance
from comtrade_io.type import CurrentBranchNum


class Line(Equipment):
    """线路部件模型"""
    bus_index: int = Field(default=0, description="母线索引号")
    rated_primary_voltage: float = Field(default=220.0, description="一次额定电压")
    rated_primary_current: float = Field(default=1.0, description="一次额定电流")
    rated_secondary_current: float = Field(default=1.0, description="二次额定电流")
    line_length: float = Field(default=0.0, description="线路长度")
    current_bran_num: CurrentBranchNum = Field(default=CurrentBranchNum.B1, description="电流分段数")
    impedance: Impedance = Field(default_factory=Impedance, description="线路阻抗")
    capacitance: Capacitance = Field(default_factory=Capacitance, description="线路电容")
    mutual_inductance: MutualInductance = Field(default_factory=MutualInductance, description="线路互感")
    currents: list[ACCBranch] = Field(default_factory=list, description="交流电流通道")
    buses: list[Bus] = Field(default_factory=list, description="关联的母线列表")

    def line2section(self) -> str:
        """将线路部件转换为线路部件模型"""
        sta_chn_str = ",".join(str(chn.index) for chn in self.stas)
        ta_chn_parts = []
        for current in self.currents:
            channels = [current.ia, current.ib, current.ic, current.i0]
            ta_chn_parts.extend(str(chn.index) for chn in channels if chn is not None)
        ta_chn_str = ",".join(ta_chn_parts)

        tv_chn_parts = []
        for bus in self.buses:
            channels = [bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.un, bus.voltage.ul]
            tv_chn_parts.extend(str(chn.index) for chn in channels if chn is not None)
        tv_chn_str = ",".join(tv_chn_parts)
        attrs = [
            f"[PRIVATELY Line_#{self.index}]",
            f"DEV_ID={self.name}",
            f"SYS_ID={self.uuid}",
            f"OBJECT_TYPE=LINE",
            f"LENGTH={self.line_length}(km)",
            f"RX={self.impedance.r1}(Ω/km),{self.impedance.x1}(Ω/km),{self.impedance.r0}(Ω/km),{self.impedance.x0}(Ω/km)",
            f"CG={self.capacitance.c1}(μf/km),{self.capacitance.g1}(S/km),{self.capacitance.c0}(μf/km),{self.capacitance.g0}(S/km)",
            f"MRX={self.mutual_inductance.mr0}(Ω/km),{self.mutual_inductance.mx0}(Ω/km)",
            f"REACTOR=-1(Ω)",
            f"TA_CHNS={ta_chn_str}",
            f"TV_CHNS={tv_chn_str}",
            f"STATUS_CHNS={sta_chn_str}"
        ]
        return "\n".join(attrs)
