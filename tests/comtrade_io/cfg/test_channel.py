import json

import pytest

from comtrade_io.cfg.channel_cfg import ChannelCfgBaseModel
from comtrade_io.type import Phase


@pytest.fixture
def channel_test_data():
    """测试数据fixture"""
    return {
        "index_ok"       : 1,
        "index_float"    : 1.0,
        "index_str"      : "a",
        "name_str"       : "模拟量1",
        "name_null"      : "",
        "phase_str_upper": "A",
        "phase_str_lower": "a",
        "phase_null"     : "",
        "phase_error"    : "x",
        "equip_str"      : "间隔",
        "equip_null"     : ""
    }


def test_str_case(channel_test_data):
    """测试正常情况下__str__方法的返回值"""
    # 创建Channel实例
    channel = ChannelCfgBaseModel(
        index=channel_test_data["index_ok"],
        name=channel_test_data["name_str"],
        phase=Phase.from_value(channel_test_data["phase_str_upper"]),
        equip=channel_test_data["equip_str"]
    )

    expected = f"{channel_test_data['index_ok']},{channel_test_data['name_str']},{channel_test_data['phase_str_upper']},{channel_test_data['equip_str']}"
    actual = str(channel)

    assert actual == expected, f"期望得到 '{expected}'，实际得到 '{actual}'"


def test_from_dict_case_param4(channel_test_data):
    """测试从字典对象中生成对象(全参数)"""
    channel_dict = {
        "index": channel_test_data["index_ok"],
        "name" : channel_test_data["name_str"],
        "phase": channel_test_data["phase_str_upper"],
        "equip": channel_test_data["equip_str"]
    }
    channel = ChannelCfgBaseModel.from_dict(channel_dict)
    assert channel.index == channel_test_data[
        "index_ok"], f"期望得到'{channel_test_data['index_ok']}'，实际得到'{channel.index}'"
    assert channel.name == channel_test_data[
        "name_str"], f"期望得到'{channel_test_data['name_str']}'，实际得到'{channel.name}'"
    assert channel.phase.value == channel_test_data[
        "phase_str_upper"], f"期望得到'{channel_test_data['phase_str_upper']}'，实际得到'{channel.phase.value}'"
    assert channel.equip == channel_test_data[
        "equip_str"], f"期望得到'{channel_test_data['equip_str']}'，实际得到'{channel.equip}'"


def test_from_dict_case_param2(channel_test_data):
    """测试从字典对象中生成对象(仅必填参数)"""
    channel_dict = {
        "index": channel_test_data["index_ok"],
        "name" : channel_test_data["name_str"]
    }
    channel = ChannelCfgBaseModel.from_dict(channel_dict)
    assert channel.index == channel_test_data[
        "index_ok"], f"期望得到'{channel_test_data['index_ok']}'，实际得到'{channel.index}'"
    assert channel.name == channel_test_data[
        "name_str"], f"期望得到'{channel_test_data['name_str']}'，实际得到'{channel.name}'"
    assert channel.phase == Phase.NONE, f"期望得到'{channel_dict.get('phase')}'，实际得到'{channel.phase}'"
    assert channel.equip == '', f"期望得到'{channel_dict.get('equip')}'，实际得到'{channel.equip}'"


def test_from_dict_case_index_float(channel_test_data):
    """测试索引号为浮点情况下的错误"""
    channel_dict = {
        "index": channel_test_data["index_float"],
        "name" : channel_test_data["name_str"],
        "phase": channel_test_data["phase_str_upper"],
        "equip": channel_test_data["equip_str"]
    }
    channel = ChannelCfgBaseModel.from_dict(channel_dict)
    assert channel.index == int(
        channel_test_data["index_float"]), f"期望得到'{channel_test_data['index_ok']}'，实际得到'{channel.index}'"


def test_from_dict_case_name_null(channel_test_data):
    """测试name必填字段为空的情况"""
    channel_dict = {
        "index": channel_test_data["index_float"]
    }
    with pytest.raises(ValueError):
        ChannelCfgBaseModel.from_dict(channel_dict)


def test_from_dict_case_phase_error(channel_test_data):
    """测试phase字典转换失败"""
    channel_dict = {
        "index": channel_test_data["index_ok"],
        "name" : channel_test_data["name_str"],
        "phase": channel_test_data["phase_error"],
        "equip": channel_test_data["equip_str"]
    }
    with pytest.raises(ValueError):
        ChannelCfgBaseModel.from_dict(channel_dict)


def test_from_json_case_param4(channel_test_data):
    """测试从json字符串中生成对象(全参数)"""
    json_str = """{
        "index": 1,
        "name" : "模拟量1",
        "phase": "A",
        "equip": "模拟量"
    }"""
    channel = ChannelCfgBaseModel.from_json(json_str)
    assert channel.index == 1, f"期望得到'1'，实际得到'{channel.index}'"
    assert channel.name == "模拟量1", f"期望得到'模拟量1'，实际得到'{channel.name}'"
    assert channel.phase.value == "A", f"期望得到'A'，实际得到'{channel.phase}'"
    assert channel.equip == "模拟量", f"期望得到'模拟量'，实际得到'{channel.equip}'"


def test_from_json_case_param2(channel_test_data):
    """测试从json字符串中生成对象(仅必填参数)"""
    json_str = """{
                "index": 1,
                "name" : "模拟量1"
            }"""
    channel = ChannelCfgBaseModel.from_json(json_str)
    assert channel.index == 1, f"期望得到'1'，实际得到'{channel.index}'"
    assert channel.name == "模拟量1", f"期望得到'模拟量1'，实际得到'{channel.name}'"
    assert channel.phase.value == "", f"期望得到'A'，实际得到'{channel.phase}'"
    assert channel.equip == "", f"期望得到'模拟量'，实际得到'{channel.equip}'"


def test_from_str_case_ok(channel_test_data):
    """测试从逗号分隔的字符串中生成对象"""
    _str = f"{channel_test_data['index_ok']},{channel_test_data['name_str']},{channel_test_data['phase_str_upper']},{channel_test_data['equip_str']}"
    channel = ChannelCfgBaseModel.from_str(_str)
    assert channel.index == channel_test_data["index_ok"], f"期望得到'1'，实际得到'{channel.index}'"


def test_from_str_case_index_error(channel_test_data):
    """测试从逗号分隔的字符串中生成(index错误)"""
    _str = f"{channel_test_data['index_str']},{channel_test_data['name_str']},{channel_test_data['phase_str_upper']},{channel_test_data['equip_str']}"
    with pytest.raises(ValueError):
        ChannelCfgBaseModel.from_str(_str)


def test_from_str_case_param2(channel_test_data):
    """测试从逗号分隔的字符串中生成对象(仅必填参数)"""
    _str = f"{channel_test_data['index_ok']},{channel_test_data['name_str']}"
    channel = ChannelCfgBaseModel.from_str(_str)
    assert channel.index == channel_test_data[
        "index_ok"], f"期望得到'{channel_test_data['index_ok']}'，实际得到'{channel.index}'"
    assert channel.name == channel_test_data[
        "name_str"], f"期望得到'{channel_test_data['name_str']}'，实际得到'{channel.name}'"
    assert channel.phase.value == "", f"期望得到空字符串，实际得到'{channel.phase.value}'"
    assert channel.equip == "", f"期望得到空字符串，实际得到'{channel.equip}'"


def test_from_str_case_param3(channel_test_data):
    """测试从逗号分隔的字符串中生成对象(3参数)"""
    _str = f"{channel_test_data['index_ok']},{channel_test_data['name_str']},{channel_test_data['phase_str_upper']}"
    channel = ChannelCfgBaseModel.from_str(_str)
    assert channel.index == channel_test_data["index_ok"]
    assert channel.name == channel_test_data["name_str"]
    assert channel.phase.value == channel_test_data["phase_str_upper"]
    assert channel.equip == ""


def test_from_str_case_phase_lower(channel_test_data):
    """测试从逗号分隔的字符串中生成(phase小写)"""
    _str = f"{channel_test_data['index_ok']},{channel_test_data['name_str']},{channel_test_data['phase_str_lower']},{channel_test_data['equip_str']}"
    channel = ChannelCfgBaseModel.from_str(_str)
    assert channel.phase.value == channel_test_data[
        "phase_str_upper"], f"期望得到'{channel_test_data['phase_str_upper']}'，实际得到'{channel.phase.value}'"


def test_from_str_case_phase_none(channel_test_data):
    """测试从逗号分隔的字符串中生成(phase为空)"""
    _str = f"{channel_test_data['index_ok']},{channel_test_data['name_str']},{channel_test_data['phase_null']},{channel_test_data['equip_str']}"
    channel = ChannelCfgBaseModel.from_str(_str)
    assert channel.phase == Phase.NONE, f"期望得到Phase.NONE，实际得到'{channel.phase}'"


def test_from_str_case_empty_string(channel_test_data):
    """测试空字符串"""
    with pytest.raises(ValueError):
        ChannelCfgBaseModel.from_str("")


def test_from_str_case_no_comma(channel_test_data):
    """测试无逗号字符串"""
    with pytest.raises(ValueError):
        ChannelCfgBaseModel.from_str("test")


def test_from_str_case_too_few_fields(channel_test_data):
    """测试字段过少"""
    with pytest.raises(ValueError):
        ChannelCfgBaseModel.from_str("1")


def test_from_dict_case_phase_lowercase(channel_test_data):
    """测试字典中phase为小写字母"""
    channel_dict = {
        "index": channel_test_data["index_ok"],
        "name" : channel_test_data["name_str"],
        "phase": channel_test_data["phase_str_lower"],
        "equip": channel_test_data["equip_str"]
    }
    channel = ChannelCfgBaseModel.from_dict(channel_dict)
    assert channel.phase.value == channel_test_data["phase_str_upper"]


def test_from_dict_case_phase_none_string(channel_test_data):
    """测试字典中phase为空字符串"""
    channel_dict = {
        "index": channel_test_data["index_ok"],
        "name" : channel_test_data["name_str"],
        "phase": channel_test_data["phase_null"],
        "equip": channel_test_data["equip_str"]
    }
    channel = ChannelCfgBaseModel.from_dict(channel_dict)
    assert channel.phase == Phase.NONE


def test_from_json_case_invalid_json(channel_test_data):
    """测试无效的JSON字符串"""
    json_str = "{ invalid json }"
    with pytest.raises(json.JSONDecodeError):
        ChannelCfgBaseModel.from_json(json_str)


def test_phase_enum_all_values(channel_test_data):
    """测试Phase枚举的所有值"""
    test_cases = [
        ("A", Phase.PHASE_A),
        ("a", Phase.PHASE_A),
        ("B", Phase.PHASE_B),
        ("b", Phase.PHASE_B),
        ("C", Phase.PHASE_C),
        ("c", Phase.PHASE_C),
        ("N", Phase.PHASE_N),
        ("n", Phase.PHASE_N),
        ("", Phase.NONE),
    ]
    for input_value, expected_phase in test_cases:
        result = Phase.from_value(input_value)
        assert result == expected_phase, f"输入'{input_value}'期望得到{expected_phase}"


def test_phase_enum_error(channel_test_data):
    """测试Phase枚举错误值"""
    with pytest.raises(ValueError):
        Phase.from_value(channel_test_data["phase_error"])
