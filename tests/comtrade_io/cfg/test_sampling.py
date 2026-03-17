import pytest

from comtrade_io.cfg.nrate import Nrate
from comtrade_io.cfg.sampling import Sampling


def test_str_full():
    nr1 = Nrate(samp=1920, end_point=1000)
    nr2 = Nrate(samp=3840, end_point=2000)
    s = Sampling(freq=60.0, nrates=[nr1, nr2])
    assert str(s) == "60.0\n2\n1920,1000\n3840,2000"


def test_str_no_nrates():
    s = Sampling(freq=50.0, nrates=[])
    assert str(s) == "50.0"


def test_from_str_case():
    s = "60\n2\n1920,1000\n3840,2000"
    sampling = Sampling.from_str(s)
    assert sampling.freq == 60.0
    assert len(sampling.nrates) == 2
    assert sampling.nrates[0].samp == 1920
    assert sampling.nrates[0].end_point == 1000
    assert sampling.nrates[1].samp == 3840


def test_from_str_only_freq():
    s = "60"
    sampling = Sampling.from_str(s)
    assert sampling.freq == 60.0
    assert len(sampling.nrates) == 0


def test_from_dict_case():
    data = {
        "freq"  : 60.0,
        "nrates": [
            {"samp": 1920, "end_point": 1000},
            {"samp": 3840, "end_point": 2000}
        ]
    }
    sampling = Sampling.from_dict(data)
    assert len(sampling.nrates) == 2
    assert sampling.nrates[0].samp == 1920
    assert sampling.nrates[1].end_point == 2000


def test_from_dict_with_str_nrates():
    data = {
        "freq"  : 60.0,
        "nrates": ["1920,1000", "3840,2000"]
    }
    sampling = Sampling.from_dict(data)
    assert len(sampling.nrates) == 2
    assert sampling.nrates[0].samp == 1920
    assert sampling.nrates[1].end_point == 2000


def test_from_json_case():
    json_str = '{"freq":60,"nrates":[{"samp":1920,"end_point":1000},{"samp":3840,"end_point":2000}]}'
    sampling = Sampling.from_json(json_str)
    assert sampling.freq == 60.0
    assert len(sampling.nrates) == 2


def test_from_dict_invalid_item():
    data = {"freq": 60.0, "nrates": [123]}
    with pytest.raises(ValueError):
        Sampling.from_dict(data)


def test_from_str_invalid_nrates():
    with pytest.raises(ValueError):
        Sampling.from_str("60\\nnot_a_rate")


# New compatibility tests for add_nrate and normalization
def test_add_nrate_with_length_endpoints():
    nr1 = Nrate(samp=1920, end_point=1000)
    s = Sampling(freq=60.0, nrates=[nr1])
    nr2 = Nrate(samp=3840, end_point=1000)
    s.add_nrate(nr2)
    assert len(s.nrates) == 2
    assert s.nrates[0].end_point == 1000
    assert s.nrates[1].end_point == 2000


def test_add_nrate_with_absolute_end():
    nr1 = Nrate(samp=1920, end_point=1000)
    s = Sampling(freq=60.0, nrates=[nr1])
    nr3 = Nrate(samp=5760, end_point=3000)
    s.add_nrate(nr3)
    assert s.nrates[-1].end_point == 3000


def test_normalization_on_from_dict_with_length():
    data = {
        "freq"  : 60.0,
        "nrates": [
            {"samp": 1920, "end_point": 1000},
            {"samp": 3840, "end_point": 1000},
        ],
    }
    s = Sampling.from_dict(data)
    assert len(s.nrates) == 2
    assert s.nrates[1].end_point == 2000
