#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Digital CFG tests using JSON test data."""

from __future__ import annotations

import json
from pathlib import Path

from comtrade_io.channel.status import Status
from comtrade_io.type import Contact, Phase


def _load_test_data() -> dict:
    repo_root = Path(__file__).resolve().parents[3]  # tests directory
    data_path = repo_root / 'data' / 'digital_test_data.json'
    if not data_path.exists():
        return {"strings": [], "dicts": []}
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def test_digital_from_str_variants():
    data = _load_test_data()
    for case in data.get('strings', []):
        s = case['input']
        expected = case['expected']
        d = Status.from_str(s)
        exp_phase = Phase.from_value(expected.get('phase',""))
        exp_contact = Contact.from_value(expected.get('contact',0))
        assert d.index == expected['index']
        assert d.name == expected['name']
        assert d.phase == exp_phase
        assert d.equip == expected.get('equip', '')
        assert d.contact == exp_contact
        s_out = str(d)
        assert isinstance(s_out, str) and len(s_out) > 0


def test_digital_from_dict_variants():
    data = _load_test_data()
    for case in data.get('dicts', []):
        d = case['input']
        exp = case['expected']
        digital = Status(
            index=d['index'],
            name=d['name'],
            phase=Phase.from_value(d.get('phase'), Phase.NONE),
            equip=d.get('equip', ''),
            contact=Contact.from_value(d.get('contact'), Contact.NormallyOpen),
        )
        assert digital.index == exp['index']
        assert digital.name == exp['name']
        assert digital.phase == Phase.from_value(exp['phase'], Phase.NONE)
        assert digital.equip == exp.get('equip', '')
        assert digital.contact == Contact.from_value(exp['contact'], Contact.NormallyOpen)
        assert isinstance(str(digital), str)
