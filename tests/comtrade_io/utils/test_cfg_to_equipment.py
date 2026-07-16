#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.model.channel import Analog, Status
from comtrade_io.model.configure import Configure
from comtrade_io.model.type import (
    AnalogChannelFlag,
    AnalogChannelType,
    DigitalChannelFlag,
    DigitalChannelType,
    Phase,
    Unit,
)
from comtrade_io.utils.cfg_to_equipment import CfgToEquipment


def _cfg(
    analogs: list[Analog] | None = None,
    statuses: list[Status] | None = None,
) -> Configure:
    cfg = Configure()
    if analogs:
        for a in analogs:
            cfg.analogs[a.index] = a
    if statuses:
        for s in statuses:
            cfg.statuses[s.index] = s
    return cfg


def _analog(
    index: int,
    name: str,
    phase: Phase,
    unit: Unit = Unit.NONE,
    primary: float = 1.0,
    secondary: float = 1.0,
    equip: str | None = None,
    type: AnalogChannelType | None = None,
    flag: AnalogChannelFlag | None = None,
) -> Analog:
    return Analog(
        index=index,
        name=name,
        phase=phase,
        unit=unit,
        primary=primary,
        secondary=secondary,
        equip=equip,
        type=type,
        flag=flag,
    )


def _status(
    index: int,
    name: str,
    equip: str | None = None,
    type: DigitalChannelType | None = None,
    flag: DigitalChannelFlag | None = None,
) -> Status:
    return Status(
        index=index,
        name=name,
        equip=equip,
        type=type,
        flag=flag,
    )


class TestCfgToEquipment:
    """CfgToEquipment 转换逻辑测试"""

    def test_empty_config(self):
        eg = CfgToEquipment.convert(_cfg())
        assert eg.buses is None
        assert eg.lines is None
        assert eg.transformers is None

    def test_bus_from_voltage_channels(self):
        cfg = _cfg(
            analogs=[
                _analog(
                    1,
                    "220kV潞北I线2211电压Ua",
                    Phase.PHASE_A,
                    Unit.V,
                    primary=220000,
                    secondary=100,
                ),
                _analog(2, "220kV潞北I线2211电压Ub", Phase.PHASE_B, Unit.V),
                _analog(3, "220kV潞北I线2211电压Uc", Phase.PHASE_C, Unit.V),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.buses is not None and len(eg.buses) == 1
        bus = eg.buses[0]
        assert bus.name == "潞北I线"
        assert bus.rated_primary_voltage == 220.0
        assert bus.rated_secondary_voltage == 100
        assert bus.voltage.ua is not None
        assert bus.voltage.ub is not None
        assert bus.voltage.uc is not None
        assert eg.lines is None

    def test_bus_requires_three_phases(self):
        cfg = _cfg(
            analogs=[
                _analog(1, "220kV潞北I线2211电压Ua", Phase.PHASE_A, Unit.V),
                _analog(2, "220kV潞北I线2211电压Ub", Phase.PHASE_B, Unit.V),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.buses is None

    def test_line_from_current_channels(self):
        cfg = _cfg(
            analogs=[
                _analog(
                    11,
                    "500kV 5041线路5P_Ia",
                    Phase.PHASE_A,
                    Unit.A,
                    primary=600,
                    secondary=1,
                ),
                _analog(12, "500kV 5041线路5P_Ib", Phase.PHASE_B, Unit.A),
                _analog(13, "500kV 5041线路5P_Ic", Phase.PHASE_C, Unit.A),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.lines is not None and len(eg.lines) == 1
        line = eg.lines[0]
        assert line.name == "5041线路"
        assert line.rated_primary_current == 600
        assert line.rated_secondary_current == 1
        assert line.rated_primary_voltage == 500.0
        assert len(line.currents) == 1
        assert line.currents[0].ia is not None
        assert line.currents[0].ib is not None
        assert line.currents[0].ic is not None

    def test_line_requires_three_phases(self):
        cfg = _cfg(
            analogs=[
                _analog(11, "500kV 5041线路5P_Ia", Phase.PHASE_A, Unit.A),
                _analog(12, "500kV 5041线路5P_Ib", Phase.PHASE_B, Unit.A),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.lines is None

    def test_transformer_two_windings(self):
        cfg = _cfg(
            analogs=[
                _analog(21, "1号主变高压侧电流Ia", Phase.PHASE_A, Unit.A, primary=600),
                _analog(22, "1号主变高压侧电流Ib", Phase.PHASE_B, Unit.A),
                _analog(23, "1号主变高压侧电流Ic", Phase.PHASE_C, Unit.A),
                _analog(24, "1号主变低压侧电流Ia", Phase.PHASE_A, Unit.A, primary=1500),
                _analog(25, "1号主变低压侧电流Ib", Phase.PHASE_B, Unit.A),
                _analog(26, "1号主变低压侧电流Ic", Phase.PHASE_C, Unit.A),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.transformers is not None and len(eg.transformers) == 1
        tr = eg.transformers[0]
        assert tr.name == "1号主变"
        assert tr.winding_num == 2
        hw = [w for w in tr.trans_winds if w.trans_wind_location.name == "HIGH"][0]
        lw = [w for w in tr.trans_winds if w.trans_wind_location.name == "LOW"][0]
        assert hw.rated_current == 600
        assert lw.rated_current == 1500

    def test_transformer_requires_abc_per_winding(self):
        cfg = _cfg(
            analogs=[
                _analog(21, "1号主变高压侧电流Ia", Phase.PHASE_A, Unit.A),
                _analog(22, "1号主变高压侧电流Ib", Phase.PHASE_B, Unit.A),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.transformers is None

    def test_transformer_with_voltage_channels(self):
        cfg = _cfg(
            analogs=[
                _analog(
                    1,
                    "220kV1号主变高压侧电压Ua",
                    Phase.PHASE_A,
                    Unit.V,
                    primary=220000,
                    secondary=100,
                ),
                _analog(
                    2,
                    "220kV1号主变高压侧电压Ub",
                    Phase.PHASE_B,
                    Unit.V,
                    primary=220000,
                    secondary=100,
                ),
                _analog(
                    3,
                    "220kV1号主变高压侧电压Uc",
                    Phase.PHASE_C,
                    Unit.V,
                    primary=220000,
                    secondary=100,
                ),
                _analog(21, "1号主变高压侧电流Ia", Phase.PHASE_A, Unit.A),
                _analog(22, "1号主变高压侧电流Ib", Phase.PHASE_B, Unit.A),
                _analog(23, "1号主变高压侧电流Ic", Phase.PHASE_C, Unit.A),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.transformers is not None and len(eg.transformers) == 1
        tr = eg.transformers[0]
        assert len(tr.acvs) == 3
        hw = tr.trans_winds[0]
        assert hw.voltage.ua is not None and hw.voltage.ua.index == 1
        assert hw.voltage.ub is not None and hw.voltage.ub.index == 2
        assert hw.voltage.uc is not None and hw.voltage.uc.index == 3

    def test_unused_status_channels_skipped(self):
        cfg = _cfg(
            statuses=[_status(1, "开关量12")],
            analogs=[
                _analog(1, "220kV潞北I线2211电压Ua", Phase.PHASE_A, Unit.V),
                _analog(2, "220kV潞北I线2211电压Ub", Phase.PHASE_B, Unit.V),
                _analog(3, "220kV潞北I线2211电压Uc", Phase.PHASE_C, Unit.V),
            ],
        )
        eg = CfgToEquipment.convert(cfg)
        assert len(eg.buses[0].stas) == 0

    def test_unused_analog_channels_skipped(self):
        cfg = _cfg(analogs=[_analog(1, "14", Phase.PHASE_A)])
        eg = CfgToEquipment.convert(cfg)
        assert eg.buses is None
        assert eg.lines is None
        assert eg.transformers is None

    def test_empty_equip_filled_from_analog(self):
        ch = _analog(1, "220kV潞北I线2211电压Ua", Phase.PHASE_A, Unit.V, equip=None)
        cfg = _cfg(analogs=[ch])
        CfgToEquipment.convert(cfg)
        assert ch.equip == "潞北I线"

    def test_empty_equip_filled_from_status(self):
        st = _status(1, "220kV母差CSC-150D保护母差动作", equip=None)
        cfg = _cfg(
            statuses=[st],
            analogs=[
                _analog(1, "220kV潞北I线2211电压Ua", Phase.PHASE_A, Unit.V),
                _analog(2, "220kV潞北I线2211电压Ub", Phase.PHASE_B, Unit.V),
                _analog(3, "220kV潞北I线2211电压Uc", Phase.PHASE_C, Unit.V),
            ],
        )
        CfgToEquipment.convert(cfg)
        assert st.equip == "母差"

    def test_status_associated_with_bus(self):
        cfg = _cfg(
            statuses=[_status(1, "潞北I线保护动作", equip="潞北I线")],
            analogs=[
                _analog(1, "220kV潞北I线2211电压Ua", Phase.PHASE_A, Unit.V),
                _analog(2, "220kV潞北I线2211电压Ub", Phase.PHASE_B, Unit.V),
                _analog(3, "220kV潞北I线2211电压Uc", Phase.PHASE_C, Unit.V),
            ],
        )
        eg = CfgToEquipment.convert(cfg)
        assert len(eg.buses[0].stas) == 1
        assert eg.buses[0].stas[0].index == 1

    def test_bus_and_line_coexist(self):
        cfg = _cfg(
            analogs=[
                _analog(1, "220kV潞北I线2211电压Ua", Phase.PHASE_A, Unit.V),
                _analog(2, "220kV潞北I线2211电压Ub", Phase.PHASE_B, Unit.V),
                _analog(3, "220kV潞北I线2211电压Uc", Phase.PHASE_C, Unit.V),
                _analog(11, "500kV 5041线路5P_Ia", Phase.PHASE_A, Unit.A),
                _analog(12, "500kV 5041线路5P_Ib", Phase.PHASE_B, Unit.A),
                _analog(13, "500kV 5041线路5P_Ic", Phase.PHASE_C, Unit.A),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert len(eg.buses) == 1
        assert len(eg.lines) == 1

    def test_transformer_by_bian_keyword(self):
        cfg = _cfg(
            analogs=[
                _analog(21, "#2主变高压侧电流Ia", Phase.PHASE_A, Unit.A),
                _analog(22, "#2主变高压侧电流Ib", Phase.PHASE_B, Unit.A),
                _analog(23, "#2主变高压侧电流Ic", Phase.PHASE_C, Unit.A),
            ]
        )
        eg = CfgToEquipment.convert(cfg)
        assert eg.transformers is not None and len(eg.transformers) == 1
