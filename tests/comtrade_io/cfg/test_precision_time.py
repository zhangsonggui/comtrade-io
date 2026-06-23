from datetime import datetime

import pytest

from comtrade_io.parser.description import DateTimeParser
from comtrade_io.parser.description.date_time_parser import (
    format_datetime_for_cfg,
)


def test_str_format_consistency():
    dt = datetime(2020, 12, 31, 23, 59, 59, 123456)
    assert format_datetime_for_cfg(dt) == dt.strftime("%m/%d/%Y,%H:%M:%S.%f")


def test_from_str_all_formats():
    dt = datetime(2020, 12, 31, 23, 59, 59, 123456)
    formats_to_test = [
        "%d/%m/%Y,%H:%M:%S.%f",
        "%Y/%m/%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S.%f",
    ]
    for fmt in formats_to_test:
        s = dt.strftime(fmt)
        result = DateTimeParser.from_str(s)
        assert result == dt


def test_from_json_case():
    dt = datetime(2020, 12, 31, 23, 59, 59, 987654)
    json_str = '{"time": "2020-12-31 23:59:59.987654"}'
    result = DateTimeParser.from_json(json_str)
    assert result == dt


def test_from_json_missing_field():
    json_str = '{}'
    with pytest.raises(Exception):
        DateTimeParser.from_json(json_str)


def test_from_str_no_microseconds():
    dt = datetime(2020, 12, 31, 23, 59, 59, 0)
    s = dt.strftime("%Y-%m-%d %H:%M:%S")
    result = DateTimeParser.from_str(s)
    assert result == dt


def test_from_str_invalid():
    with pytest.raises(ValueError):
        DateTimeParser.from_str("not-a-date")
