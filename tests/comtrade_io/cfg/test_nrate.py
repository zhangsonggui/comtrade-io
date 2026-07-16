import pytest
from pydantic import ValidationError

from comtrade_io.model.description import Segment
from comtrade_io.parser.description import SegmentParser


def test_from_str_case():
    nr = SegmentParser.from_str("1920,1000")
    assert nr is not None
    assert nr.samp == 1920
    assert nr.end_point == 1000


def test_from_str_insufficient():
    result = SegmentParser.from_str("1920")
    assert result is None


def test_from_dict_case():
    data = {"samp": 1920, "end_point": 1000}
    nr = SegmentParser.from_dict(data)
    assert nr.samp == 1920
    assert nr.end_point == 1000


def test_from_dict_missing_field():
    data = {"samp": 1920}  # 缺少 end_point
    with pytest.raises(ValueError):
        SegmentParser.from_dict(data)


def test_from_json_case():
    json_str = '{"samp": 1920, "end_point": 1000}'
    nr = SegmentParser.from_json(json_str)
    assert nr.samp == 1920
    assert nr.end_point == 1000


def test_from_json_missing_field():
    json_str = '{"samp": 1920}'
    with pytest.raises(ValueError):
        SegmentParser.from_json(json_str)


def test_validation_negative():
    with pytest.raises(ValidationError):
        Segment(samp=0, end_point=10)
    with pytest.raises(ValidationError):
        Segment(samp=-1, end_point=10)
