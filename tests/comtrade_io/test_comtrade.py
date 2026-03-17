import pytest
from pathlib import Path
from comtrade_io.comtrade import Comtrade
from comtrade_io.type import DataType


@pytest.fixture(scope="session")
def comtrade():
    """Global Comtrade instance for all tests"""
    filename = r"../data/binary_1999.cfg"
    return Comtrade.from_file(file_name=filename)


def test_comtrade_initialization(comtrade):
    """Test Comtrade class initialization"""
    assert comtrade.file.cfg_path.path == Path(r"../data/binary_1999.cfg")
    assert comtrade.cfg.header.station == "GHBZ"
    assert comtrade.cfg.channel_num.analog == 96
    assert comtrade.cfg.data_type.value == "BINARY"


def test_get_line(comtrade):
    line = comtrade.get_line("ghx")
    assert line.index == 3
    assert line.name == "ghx"
    assert line.lin_len == 9.75
    assert line.bran_num.value == 1
    assert line.rx.r0 == 0.062
    assert line.rx.r1 == 0.021
    assert line.currents[0].idx == 1
    assert line.currents[0].dir.name == "POS"
    assert line.currents[0].ia.index == 25
    assert line.currents[0].ib.index == 26
    assert line.currents[0].ic.index == 27
    assert line.currents[0].i0.index == 28
    assert line.buses[0].voltage.ua.index == 1
    assert line.buses[0].voltage.ub.index == 2
    assert line.buses[0].voltage.uc.index == 3
    assert line.buses[0].voltage.un.index == 4

def test_get_bus(comtrade):
    bus = comtrade.get_bus("220kV母线U")
    assert bus.index == 1
    assert bus.name == "220kV母线U"
    assert bus.v_rtg_snd_pos.value == "BUS"
    assert bus.voltage.ua.index == 1
    assert bus.voltage.ub.index == 2
    assert bus.voltage.uc.index == 3
    assert bus.voltage.un.index == 4

def test_get_transformer(comtrade):
    pass