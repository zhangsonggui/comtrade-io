#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Analog CFG tests using JSON test data."""

from __future__ import annotations

import json
from pathlib import Path

from comtrade_io.channel.analog import Analog
from comtrade_io.type import Phase, Unit
from comtrade_io.type.tran_side import TranSide


def _load_test_data() -> dict:
    repo_root = Path(__file__).resolve().parents[3]  # tests directory
    data_path = repo_root / 'data' / 'analog_test_data.json'
    if not data_path.exists():
        return {"strings": [], "dicts": []}
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_analog_from_str_variants():
    data = _load_test_data()
    for case in data.get('strings', []):
        s = case['input']
        expected = case['expected']
        a = Analog.from_str(s)
        exp_phase = Phase.from_value(expected.get('phase'), Phase.NONE)
        exp_unit = Unit.from_value(expected.get('unit'), Unit.NONE)
        exp_tran = TranSide.from_value(expected.get('tran_side'), TranSide.S)
        assert a.index == expected['index']
        assert a.name == expected['name']
        assert a.phase == exp_phase
        assert a.equip == expected.get('equip', '')
        assert a.unit == exp_unit
        assert a.multiplier == expected['multiplier']
        assert a.offset == expected['offset']
        assert a.delay == expected['delay']
        assert a.min_value == expected['min_value']
        assert a.max_value == expected['max_value']
        assert a.primary == expected['primary']
        assert a.secondary == expected['secondary']
        assert a.tran_side == exp_tran
        s_out = str(a)
        assert isinstance(s_out, str) and len(s_out) > 0


def test_analog_from_dict_variants():
    data = _load_test_data()
    for case in data.get('dicts', []):
        d = case['input']
        exp = case['expected']
        a = Analog(
            index=d['index'],
            name=d['name'],
            phase=Phase.from_value(d.get('phase'), Phase.NONE),
            equip=d.get('equip', ''),
            unit=Unit.from_value(d.get('unit'), Unit.NONE),
            multiplier=d.get('multiplier', 1.0),
            offset=d.get('offset', 0.0),
            delay=d.get('delay', 0.0),
            min_value=d.get('min_value', 0.0),
            max_value=d.get('max_value', 0.0),
            primary=d.get('primary', 1.0),
            secondary=d.get('secondary', 1.0),
            tran_side=TranSide.from_value(d.get('tran_side'), TranSide.S),
        )
        assert a.index == exp['index']
        assert a.name == exp['name']
        assert a.phase == Phase.from_value(exp['phase'], Phase.NONE)
        assert a.equip == exp.get('equip', '')
        assert a.unit == Unit.from_value(exp['unit'], Unit.NONE)
        assert a.multiplier == exp['multiplier']
        assert a.offset == exp['offset']
        assert a.delay == exp['delay']
        assert a.min_value == exp['min_value']
        assert a.max_value == exp['max_value']
        assert a.primary == exp['primary']
        assert a.secondary == exp['secondary']
        assert a.tran_side == TranSide.from_value(exp['tran_side'], TranSide.S)
        assert isinstance(str(a), str)
