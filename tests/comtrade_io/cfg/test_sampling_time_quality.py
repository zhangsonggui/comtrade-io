import pytest

from comtrade_io.model.configure import Configure
from comtrade_io.model.description import SamplingTimeQuality


def test_default_values():
    stq = SamplingTimeQuality()
    assert str(stq) == "0,0"
    assert stq.decode["locked"] is True
    assert stq.decode["description"] == "正常运行，时钟锁定"
    assert stq.decode["lcapsec_description"] == "无闰秒"


def test_decode_zero():
    stq = SamplingTimeQuality(tmq_code="0", lcapsec=0)
    d = stq.decode
    assert d["locked"] is True
    assert d["description"] == "正常运行，时钟锁定"
    assert d["precision_seconds"] == 0.0


def test_decode_single_digit():
    stq = SamplingTimeQuality(tmq_code="1", lcapsec=0)
    d = stq.decode
    assert d["locked"] is False
    assert d["precision_seconds"] == pytest.approx(1e-9)
    assert "10^-9" in d["description"]


def test_decode_b():
    stq = SamplingTimeQuality(tmq_code="B", lcapsec=0)
    d = stq.decode
    assert d["locked"] is False
    assert d["precision_seconds"] == pytest.approx(10.0)
    assert "10^1" in d["description"]


def test_decode_f():
    stq = SamplingTimeQuality(tmq_code="F", lcapsec=0)
    d = stq.decode
    assert d["locked"] is False
    assert d["precision_seconds"] is None
    assert d["description"] == "时钟错误，时间不可靠"


def test_lcapsec_descriptions():
    assert (
        SamplingTimeQuality(lcapsec=1).decode["lcapsec_description"]
        == "在记录中增加闰秒"
    )
    assert (
        SamplingTimeQuality(lcapsec=2).decode["lcapsec_description"]
        == "从记录中删除闰秒"
    )
    assert (
        SamplingTimeQuality(lcapsec=3).decode["lcapsec_description"]
        == "时钟源没有闰秒功能"
    )


def test_tmq_code_must_be_single_hex_digit():
    with pytest.raises(ValueError):
        SamplingTimeQuality(tmq_code="10")


def test_configure_str_outputs_default_sampling_time_quality():
    cfg_lines = str(Configure()).splitlines()
    assert cfg_lines[-2] == "+8,+8"
    assert cfg_lines[-1] == "0,0"
