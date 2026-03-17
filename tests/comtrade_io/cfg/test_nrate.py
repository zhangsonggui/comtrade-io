import pytest
from pydantic import ValidationError

from comtrade_io.cfg.nrate import Nrate


def test_from_str_case():
    nr = Nrate.from_str("1920,1000")
    assert nr.samp == 1920
    assert nr.end_point == 1000


def test_from_str_insufficient():
    with pytest.raises(ValueError):
        Nrate.from_str("1920")  # 只有一个部分


def test_from_dict_case():
    data = {"samp": 1920, "end_point": 1000}
    nr = Nrate.from_dict(data)
    assert nr.samp == 1920
    assert nr.end_point == 1000


def test_from_dict_missing_field():
    data = {"samp": 1920}  # 缺少 end_point
    with pytest.raises(ValueError):
        Nrate.from_dict(data)


def test_from_json_case():
    json_str = '{"samp": 1920, "end_point": 1000}'
    nr = Nrate.from_json(json_str)
    assert nr.samp == 1920
    assert nr.end_point == 1000


def test_from_json_missing_field():
    json_str = '{"samp": 1920}'
    with pytest.raises(ValueError):
        Nrate.from_json(json_str)


def test_validation_negative():
    with pytest.raises(ValidationError):
        Nrate(samp=0, end_point=10)
    # 也可以测试负数场景
    with pytest.raises(ValidationError):
        Nrate(samp=-1, end_point=10)
