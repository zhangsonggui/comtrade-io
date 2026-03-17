import pytest

from comtrade_io.cfg.channel_num import ChannelNum


def test_str_full():
    cn = ChannelNum(total=288, analog=96, digital=192)
    assert str(cn) == "288,96A,192D"


def test_from_str_full():
    s = "288,96A,192D"
    cn = ChannelNum.from_str(s)
    assert cn.total == 288
    assert cn.analog == 96
    assert cn.digital == 192


def test_from_str_inconsistent():
    with pytest.raises(ValueError):
        ChannelNum.from_str("289,96A,192D")


def test_from_dict():
    data = {"total": 288, "analog": 96, "digital": 192}
    cn = ChannelNum.from_dict(data)
    assert cn.total == 288
    assert cn.analog == 96
    assert cn.digital == 192


def test_from_json_case():
    json_str = '{"total": 288, "analog": 96, "digital": 192}'
    cn = ChannelNum.from_json(json_str)
    assert cn.total == 288
    assert cn.analog == 96
    assert cn.digital == 192


def test_from_dict_missing_field():
    data = {"total": 288, "analog": 96}  # missing digital
    with pytest.raises(ValueError):
        ChannelNum.from_dict(data)


def test_from_json_missing_field():
    json_str = '{"total": 288, "analog": 96}'  # missing digital
    with pytest.raises(ValueError):
        ChannelNum.from_json(json_str)
