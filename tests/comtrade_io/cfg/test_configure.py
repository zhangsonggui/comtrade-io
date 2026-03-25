#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
from pathlib import Path

import pytest

from comtrade_io.cfg import Configure
from comtrade_io.type import Version

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CFG_FILE = DATA_DIR / "binary_1999.cfg"

@pytest.fixture(scope="session")
def config():
    config = Configure.from_file(file_name=CFG_FILE)
    return config

def test_config_header(config):
    assert config.header.station == "GHBZ"
    assert config.header.recorder == "220kV线路故障"
    assert config.header.version == Version.V1999

def test_config_channel_num(config):
    assert config.channel_num.analog == 96
    assert config.channel_num.digital == 192
    assert config.channel_num.total == 288


def test_config_analog(config):
    an = config.analogs.get(8)
    assert an.index == 8
    assert an.name == "35kV母线Ⅰ_3U0"
    assert an.phase.value == "N"
    assert an.max_value == 32767
    assert an.min_value == -32767
    assert an.primary == 11662.47
    assert an.secondary == 57.735
    assert an.tran_side.value == "S"

def test_config_digital(config):
    dn = config.digitals.get(21)
    assert dn.name == "220kV母差保护一_I母差动动作"
    assert dn.contact.value == "0"

def test_config_sampling(config):
    samp = config.sampling
    assert len(samp.segments) == 1
    assert samp.segments[0].end_point == 45600

def test_config_time(config):
    assert config.start_time.time == datetime.datetime(year=2023,month=5,day=12,hour=19,minute=45,second=25,microsecond=600000)
    assert config.fault_time.time == datetime.datetime(year=2023,month=5,day=12,hour=19,minute=45,second=25,microsecond=814600)

def test_config_data_type(config):
    assert config.data_type.value == "BINARY"

def test_config_timemult(config):
    assert config.timemult == 1
