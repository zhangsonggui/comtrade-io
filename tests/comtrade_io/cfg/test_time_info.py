import pytest

from comtrade_io.cfg.time_info import TimeInfo


def test_str_format_consistency():
    ti = TimeInfo(time_code='A1B2', local_code='UTC5')
    assert str(ti) == 'A1B2,UTC5'


def test_from_str():
    ti = TimeInfo.from_str('X9Y2,UTC+0')
    assert ti.time_code == 'X9Y2'
    assert ti.local_code == 'UTC+0'


def test_from_json_case():
    json_str = '{"time_code": "L1", "local_code": "UTC-1"}'
    ti = TimeInfo.from_json(json_str)
    assert ti.time_code == 'L1'
    assert ti.local_code == 'UTC-1'


def test_from_json_missing_field():
    json_str = '{}'
    with pytest.raises(Exception):
        TimeInfo.from_json(json_str)


def test_from_str_invalid():
    with pytest.raises(ValueError):
        TimeInfo.from_str('ONLYONE')
