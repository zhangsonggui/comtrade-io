import pytest

from comtrade_io.cfg.sampling_time_quality import SamplingTimeQuality


def test_decode_zero():
    stq = SamplingTimeQuality(tmq_code='0', lcapsec=0)
    d = stq.decode
    assert d['locked'] is True
    assert '正常运行' in d['description']
    assert d['precision_seconds'] == 0.0


def test_decode_f():
    stq = SamplingTimeQuality(tmq_code='F', lcapsec=0)
    d = stq.decode
    assert d['locked'] is False
    assert '不可置信' in d['description']


def test_decode_single_digit():
    stq = SamplingTimeQuality(tmq_code='1', lcapsec=0)
    d = stq.decode
    assert d['precision_seconds'] == pytest.approx(1e-9)
    assert '10^-9' in d['description']


def test_decode_ten():
    stq = SamplingTimeQuality(tmq_code='A', lcapsec=0)
    d = stq.decode
    assert d['value'] == 10
    assert d['precision_seconds'] == 1.0
    assert '10^0' in d['description']


def test_decode_twelve():
    stq = SamplingTimeQuality(tmq_code='C', lcapsec=0)
    d = stq.decode
    assert d['value'] == 12
    assert d['precision_seconds'] == 100.0
    assert '10^2' in d['description']
