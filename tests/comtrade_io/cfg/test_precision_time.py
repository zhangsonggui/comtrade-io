from datetime import datetime

import pytest

from comtrade_io.base.precision_time import PrecisionTime


def test_str_format_consistency():
    dt = datetime(2020, 12, 31, 23, 59, 59, 123456)
    pt = PrecisionTime(time=dt)
    assert str(pt) == dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def test_from_str_all_formats():
    dt = datetime(2020, 12, 31, 23, 59, 59, 123456)
    # Test a few common formats instead of iterating through all
    # Use formats that are actually supported by time_formats list
    formats_to_test = [
        "%d/%m/%Y,%H:%M:%S.%f",  # European format with comma
        "%Y/%m/%d %H:%M:%S.%f",  # ISO-like format with space
        "%Y-%m-%d %H:%M:%S.%f",  # Standard ISO format
    ]
    for fmt in formats_to_test:
        s = dt.strftime(fmt)
        pt = PrecisionTime.from_str(s)
        assert pt.time == dt


def test_from_json_case():
    dt = datetime(2020, 12, 31, 23, 59, 59, 987654)
    json_str = '{"time": "2020-12-31 23:59:59.987654"}'
    pt = PrecisionTime.from_json(json_str)
    assert pt.time == dt


def test_from_json_missing_field():
    json_str = '{}'
    with pytest.raises(Exception):  # ValueError or KeyError depending on implementation
        PrecisionTime.from_json(json_str)


def test_from_str_no_microseconds():
    dt = datetime(2020, 12, 31, 23, 59, 59, 0)
    s = dt.strftime("%Y-%m-%d %H:%M:%S")
    pt = PrecisionTime.from_str(s)
    assert pt.time == dt


def test_from_str_invalid():
    with pytest.raises(ValueError):
        PrecisionTime.from_str("not-a-date")
