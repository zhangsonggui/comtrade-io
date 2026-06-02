from datetime import datetime

import pytest

from comtrade_io.model.description import PrecisionTime
from comtrade_io.parser.description import PrecisionTimeParser

def test_str_format_consistency():
    dt = datetime(2020, 12, 31, 23, 59, 59, 123456)
    pt = PrecisionTime(time=dt)
    assert str(pt) == dt.strftime("%m/%d/%Y,%H:%M:%S.%f")


def test_from_str_all_formats():
    dt = datetime(2020, 12, 31, 23, 59, 59, 123456)
    formats_to_test = [
        "%d/%m/%Y,%H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
    ]
    for fmt in formats_to_test:
        s = dt.strftime(fmt)
        pt = PrecisionTimeParser.from_str(s)
        assert pt.time == dt


def test_from_json_case():
    dt = datetime(2020, 12, 31, 23, 59, 59, 987654)
    json_str = '{"time": "2020-12-31 23:59:59.987654"}'
    pt = PrecisionTimeParser.from_json(json_str)
    assert pt.time == dt


def test_from_json_missing_field():
    json_str = '{}'
    with pytest.raises(Exception):
        PrecisionTimeParser.from_json(json_str)


def test_from_str_no_microseconds():
    dt = datetime(2020, 12, 31, 23, 59, 59, 0)
    s = dt.strftime("%Y-%m-%d %H:%M:%S")
    pt = PrecisionTimeParser.from_str(s)
    assert pt.time == dt


def test_from_str_invalid():
    with pytest.raises(ValueError):
        PrecisionTimeParser.from_str("not-a-date")
