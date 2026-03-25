import pytest

from comtrade_io.cfg.sampling import Sampling
from comtrade_io.cfg.segment import Segment


def test_str_full():
    nr1 = Segment(samp=1920, end_point=1000)
    nr2 = Segment(samp=3840, end_point=2000)
    s = Sampling(freq=60.0, segments=[nr1, nr2])
    assert str(s) == "60.0\n2\n1920,1000\n3840,2000"


def test_str_no_segment():
    s = Sampling(freq=50.0, segments=[])
    assert str(s) == "50.0"


def test_from_str_case():
    s = "60\n2\n1920,1000\n3840,2000"
    sampling = Sampling.from_str(s)
    assert sampling.freq == 60.0
    assert len(sampling.segments) == 2
    assert sampling.segments[0].samp == 1920
    assert sampling.segments[0].end_point == 1000
    assert sampling.segments[1].samp == 3840


def test_from_str_only_freq():
    s = "60"
    sampling = Sampling.from_str(s)
    assert sampling.freq == 60.0
    assert len(sampling.segments) == 0


def test_from_dict_case():
    data = {
        "freq": 60.0,
        "segments": [
            {"samp": 1920, "end_point": 1000},
            {"samp": 3840, "end_point": 2000}
        ]
    }
    sampling = Sampling.from_dict(data)
    assert len(sampling.segments) == 2
    assert sampling.segments[0].samp == 1920
    assert sampling.segments[1].end_point == 2000


def test_from_dict_with_str_segments():
    data = {
        "freq": 60.0,
        "segments": ["1920,1000", "3840,2000"]
    }
    sampling = Sampling.from_dict(data)
    assert len(sampling.segments) == 2
    assert sampling.segments[0].samp == 1920
    assert sampling.segments[1].end_point == 2000


def test_from_json_case():
    json_str = '{"freq":60,"segments":[{"samp":1920,"end_point":1000},{"samp":3840,"end_point":2000}]}'
    sampling = Sampling.from_json(json_str)
    assert sampling.freq == 60.0
    assert len(sampling.segments) == 2


def test_from_dict_invalid_item():
    data = {"freq": 60.0, "segments": [123]}
    with pytest.raises(ValueError):
        Sampling.from_dict(data)


def test_from_str_invalid_segments():
    with pytest.raises(ValueError):
        Sampling.from_str("60\\nnot_a_rate")


def test_add_segment_with_absolute_end():
    nr1 = Segment(samp=1920, end_point=1000)
    s = Sampling(freq=60.0, segments=[nr1])
    nr3 = Segment(samp=5760, end_point=3000)
    s.add_segment(nr3)
    assert s.segments[-1].end_point == 3000
