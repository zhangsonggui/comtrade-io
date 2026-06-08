import pytest

from comtrade_io.model.description import Sampling, Segment
from comtrade_io.parser.description import SamplingParser

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
    sampling = SamplingParser.from_str(s)
    assert sampling.freq == 60.0
    assert len(sampling.segments) == 2
    assert sampling.segments[0].samp == 1920
    assert sampling.segments[0].end_point == 1000
    assert sampling.segments[1].samp == 3840


def test_from_str_only_freq():
    s = "60"
    sampling = SamplingParser.from_str(s)
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
    sampling = SamplingParser.from_dict(data)
    assert len(sampling.segments) == 2
    assert sampling.segments[0].samp == 1920
    assert sampling.segments[1].end_point == 2000


def test_from_dict_with_str_segments():
    data = {
        "freq": 60.0,
        "segments": ["1920,1000", "3840,2000"]
    }
    sampling = SamplingParser.from_dict(data)
    assert len(sampling.segments) == 2
    assert sampling.segments[0].samp == 1920
    assert sampling.segments[1].end_point == 2000


def test_from_json_case():
    json_str = '{"freq":60,"segments":[{"samp":1920,"end_point":1000},{"samp":3840,"end_point":2000}]}'
    sampling = SamplingParser.from_json(json_str)
    assert sampling.freq == 60.0
    assert len(sampling.segments) == 2


def test_from_dict_invalid_item():
    data = {"freq": 60.0, "segments": [123]}
    with pytest.raises(ValueError):
        SamplingParser.from_dict(data)


def test_auto_fix_non_cumulative_end_points():
    """验证end_point为非累计值（段采样点数）时自动修正为累计值"""
    s1 = Segment(samp=10000, end_point=7000)
    s2 = Segment(samp=2000, end_point=840)
    s3 = Segment(samp=10000, end_point=4800)
    s4 = Segment(samp=2000, end_point=4000)
    sampling = Sampling(freq=50.0, segments=[s1, s2, s3, s4])
    assert sampling.segments[0].end_point == 7000
    assert sampling.segments[0].start_point == 1
    assert sampling.segments[0].count == 7000
    assert sampling.segments[1].end_point == 7840
    assert sampling.segments[1].start_point == 7001
    assert sampling.segments[1].count == 840
    assert sampling.segments[2].end_point == 12640
    assert sampling.segments[2].start_point == 7841
    assert sampling.segments[2].count == 4800
    assert sampling.segments[3].end_point == 16640
    assert sampling.segments[3].start_point == 12641
    assert sampling.segments[3].count == 4000


def test_no_fix_for_cumulative_end_points():
    """验证累计的end_point不会被错误修正"""
    s1 = Segment(samp=10000, end_point=7000)
    s2 = Segment(samp=2000, end_point=7840)
    sampling = Sampling(freq=50.0, segments=[s1, s2])
    assert sampling.segments[0].end_point == 7000
    assert sampling.segments[0].start_point is None
    assert sampling.segments[0].count is None
    assert sampling.segments[1].end_point == 7840
    assert sampling.segments[1].start_point is None
    assert sampling.segments[1].count is None

    data = {"freq": 60.0, "segments": [123]}
    with pytest.raises(ValueError):
        SamplingParser.from_dict(data)
