import pytest

from comtrade_io.utils.numeric_utils import parse_float


def test_parse_float_mixed():
    assert parse_float("34.56b") == 34.56


def test_parse_float_invalid_raises():
    with pytest.raises(ValueError):
        parse_float("abc")


def test_parse_float_with_default_for_empty():
    assert parse_float("", default=1.23) == 1.23
