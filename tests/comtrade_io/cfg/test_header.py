from comtrade_io.cfg.header import Header
from comtrade_io.type.version import Version


def test_str_case_full_params():
    header = Header(
        station="变电站X",
        recorder="录波仪X",
        version=Version.from_value("1999", Version.V1991)
    )
    expected = f"{header.station},{header.recorder},{header.version.value}"
    actual = str(header)
    assert actual == expected


def test_str_case_defaults():
    header = Header()
    assert header.station == "变电站"
    assert header.recorder == "故障录波设备"
    assert header.version == Version.V1991
    assert str(header) == f"变电站,故障录波设备,1991"


def test_from_str_case_full_params():
    _str = "变电站,故障录波设备,1999"
    header = Header.from_str(_str)
    assert header.station == "变电站"
    assert header.recorder == "故障录波设备"
    assert header.version.value == "1999"

def test_from_str_case_version_params():
    _str = "变电站,故障录波设备,2005"
    header = Header.from_str(_str)
    assert header.station == "变电站"
    assert header.recorder == "故障录波设备"
    assert header.version.value == "1991"



def test_from_str_case_params():
    _str = "变电站,故障录波设备"
    header = Header.from_str(_str)
    assert header.station == "变电站"
    assert header.recorder == "故障录波设备"
    assert header.version.value == "1991"


def test_from_dict_case():
    data = {
        "station" : "变电站",
        "recorder": "故障录波设备",
        "version" : "1999"
    }
    header = Header.from_dict(data)
    assert header.station == "变电站"
    assert header.recorder == "故障录波设备"
    assert header.version.value == "1999"


def test_from_json_case():
    json_str = '{"station":"变电站","recorder":"故障录波设备","version":"1999"}'
    header = Header.from_json(json_str)
    assert header.station == "变电站"
    assert header.recorder == "故障录波设备"
    assert header.version.value == "1999"
