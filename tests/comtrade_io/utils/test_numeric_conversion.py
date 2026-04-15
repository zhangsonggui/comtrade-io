import pytest

from comtrade_io.utils.numeric_conversion import parse_float, safe_float_convert


def test_mixed_string_extraction():
    # Should extract the first numeric substring and convert
    assert safe_float_convert("12a34", "val") == 12.0


def test_parse_float_mixed():
    assert parse_float("34.56b") == 34.56


def test_parse_float_invalid_raises():
    with pytest.raises(ValueError):
        parse_float("abc")


def test_parse_float_with_default_for_empty():
    assert parse_float("", default=1.23) == 1.23
