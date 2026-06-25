import pytest

from comtrade_io.model.type import (
    AnalogChannelFlag,
    AnalogChannelType,
    DigitalChannelFlag,
    DigitalChannelType,
)
from comtrade_io.utils.recognition.channel_recognizer import (
    RecognitionResult,
    recognize_analog_channel,
    recognize_status_channel,
)


@pytest.mark.parametrize(
    "name, voltage, monitor, channel_type, channel_flag, result",
    [
        (
            "220kV北上I线2211电压Ua",
            220000,
            "北上I线",
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.SUCCESS,
        ),
        (
            "220kV 4M#母线电压AD1 Ua",
            220000,
            "4M#母线",
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.SUCCESS,
        ),
        (
            "500kV 5041线路5P_3I0",
            500000,
            "5041线路",
            AnalogChannelType.A,
            AnalogChannelFlag.TA,
            RecognitionResult.SUCCESS,
        ),
        (
            "220kV 49PT电压Ua",
            220000,
            "49PT",
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.SUCCESS,
        ),
        (
            "直流母线电流",
            None,
            "直流母线",
            AnalogChannelType.D,
            AnalogChannelFlag.DA,
            RecognitionResult.SUCCESS,
        ),
        (
            "频率",
            None,
            None,
            AnalogChannelType.O,
            AnalogChannelFlag.FQ,
            RecognitionResult.PARTIAL,
        ),
        # ---------- 电压等级+设备名+测量量 ----------
        (
            "220kV 4甲#母线电压AD1 Ua",
            220000,
            "4甲#母线",
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.SUCCESS,
        ),
        (
            "220kV 4甲#母线电压AD1 Ub",
            220000,
            "4甲#母线",
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.SUCCESS,
        ),
        (
            "220kV 4甲#母线电压AD1 Uc",
            220000,
            "4甲#母线",
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.SUCCESS,
        ),
        # ---------- 设备名+测量量(无电压等级) ----------
        (
            "2211安题二线电流AD1 Ia",
            None,
            "2211安题二线",
            AnalogChannelType.A,
            AnalogChannelFlag.TA,
            RecognitionResult.SUCCESS,
        ),
        (
            "2211安题二线电流AD1 Ib",
            None,
            "2211安题二线",
            AnalogChannelType.A,
            AnalogChannelFlag.TA,
            RecognitionResult.SUCCESS,
        ),
        (
            "2211安题二线电流AD1 Ic",
            None,
            "2211安题二线",
            AnalogChannelType.A,
            AnalogChannelFlag.TA,
            RecognitionResult.SUCCESS,
        ),
        # ---------- 直流通道 ----------
        (
            "直流通道1（DC500V)",
            None,
            "直流通道1（DC500V)",
            AnalogChannelType.D,
            AnalogChannelFlag.DV,
            RecognitionResult.SUCCESS,
        ),
        # ---------- 数据损坏(含**) ----------
        (
            "220k5惠**241电压 Ub",
            None,
            None,
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.PARTIAL,
        ),
        (
            "220k5惠**241电压 Uc",
            None,
            None,
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.PARTIAL,
        ),
        # ---------- 其他(无设备关键字) ----------
        (
            "2246旁路电流Ia",
            None,
            None,
            AnalogChannelType.A,
            AnalogChannelFlag.TA,
            RecognitionResult.PARTIAL,
        ),
        (
            "2246旁路电流Ib",
            None,
            None,
            AnalogChannelType.A,
            AnalogChannelFlag.TA,
            RecognitionResult.PARTIAL,
        ),
        (
            "2246旁路电流Ic",
            None,
            None,
            AnalogChannelType.A,
            AnalogChannelFlag.TA,
            RecognitionResult.PARTIAL,
        ),
        # ---------- 高频通道 ----------
        (
            "2213方向保护高频信号",
            None,
            None,
            AnalogChannelType.O,
            AnalogChannelFlag.HF,
            RecognitionResult.PARTIAL,
        ),
        (
            "2214方向保护高频信号",
            None,
            None,
            AnalogChannelType.O,
            AnalogChannelFlag.HF,
            RecognitionResult.PARTIAL,
        ),
        # ---------- 频率通道(无电压关键字则识别为FQ) ----------
        (
            "频率3",
            None,
            None,
            AnalogChannelType.O,
            AnalogChannelFlag.FQ,
            RecognitionResult.PARTIAL,
        ),
        (
            "频率4",
            None,
            None,
            AnalogChannelType.O,
            AnalogChannelFlag.FQ,
            RecognitionResult.PARTIAL,
        ),
        # ---------- 频率通道(含电压关键字则识别为TV) ----------
        (
            "交流电压模拟量4频率",
            None,
            None,
            AnalogChannelType.A,
            AnalogChannelFlag.TV,
            RecognitionResult.PARTIAL,
        ),
    ],
)
def test_recognize_analog_channel(
    name, voltage, monitor, channel_type, channel_flag, result
):
    detail = recognize_analog_channel(name)

    assert detail.voltage_level == voltage
    assert detail.monitor == monitor
    assert detail.protection is None
    assert detail.channel_type == channel_type
    assert detail.channel_flag == channel_flag
    assert detail.result == result


@pytest.mark.parametrize(
    "name",
    [
        "14",
        "线路15 Ia",
        "电压3 Ua",
        "模拟量89",
        "21-4#线路Ia",
        # 通用类型+编号(未使用)
        "电流1 Ia(1A)",
        "电流1 Ib(1A)",
        "电流1 Ic(1A)",
        # 模拟量编号通道(无设备)
        "13#模拟量通道Ia",
        "14#模拟量通道Ib",
        "15#模拟量通道Ic",
        # 编号+#+类型(未使用)
        "17-1#发电机机端电压Ua",
        "18-1#发电机机端电压Ub",
        "19-1#发电机机端电压Uc",
        # 纯数字(无含义)
        "121",
        "122",
        "123",
        # 备用通道(无含义)
        "备用CT 1电流Ia",
        "备用CT 1电流Ib",
        "备用CT 1电流Ic",
    ],
)
def test_recognize_analog_channel_unused(name):
    detail = recognize_analog_channel(name)

    assert detail.voltage_level is None
    assert detail.monitor is None
    assert detail.protection is None
    assert detail.channel_type == AnalogChannelType.O
    assert detail.channel_flag == AnalogChannelFlag.NONE
    assert detail.result == RecognitionResult.UNUSED


@pytest.mark.parametrize(
    "name, channel_type, channel_flag",
    [
        ("P", AnalogChannelType.O, AnalogChannelFlag.PW),
        ("Q", AnalogChannelType.O, AnalogChannelFlag.PW),
        ("f", AnalogChannelType.O, AnalogChannelFlag.FQ),
        ("功率", AnalogChannelType.O, AnalogChannelFlag.PW),
        ("阻抗", AnalogChannelType.O, AnalogChannelFlag.ZX),
        ("直1+", AnalogChannelType.D, AnalogChannelFlag.CONST),
    ],
)
def test_analog_legacy_name_patterns_through_unified_entry(
    name, channel_type, channel_flag
):
    detail = recognize_analog_channel(name)

    assert detail.channel_type == channel_type
    assert detail.channel_flag == channel_flag


def test_recognize_status_channel_unified_result():
    detail = recognize_status_channel("220kV母差CSC-150D保护母差动作")

    assert detail.voltage_level == 220000
    assert detail.monitor == "母差"
    assert detail.protection == "CSC-150D"
    assert detail.channel_type == DigitalChannelType.Relay_Act
    assert detail.channel_flag == DigitalChannelFlag.TR
    assert detail.result == RecognitionResult.SUCCESS


def test_recognize_status_channel_unused():
    detail = recognize_status_channel("开关量12")

    assert detail.voltage_level is None
    assert detail.monitor is None
    assert detail.protection is None
    assert detail.channel_type == DigitalChannelType.Other
    assert detail.channel_flag == DigitalChannelFlag.GENERAL
    assert detail.result == RecognitionResult.UNUSED


# ---------- 以下为补充识别的边缘场景 ----------


@pytest.mark.parametrize(
    "name, channel_type, channel_flag, result",
    [
        # 编号+#+英文型号+相别 → IA/IB 可识别为电流, UN 无法识别
        ("37#IA", AnalogChannelType.A, AnalogChannelFlag.TA, RecognitionResult.PARTIAL),
        ("38#IB", AnalogChannelType.A, AnalogChannelFlag.TA, RecognitionResult.PARTIAL),
        # 编号+#+UN → 无明确电气含义 → FAILED
        (
            "16#UN",
            AnalogChannelType.O,
            AnalogChannelFlag.CONST,
            RecognitionResult.FAILED,
        ),
        # 英文AI/CT/PT通道(纯标号、无含义) → FAILED
        (
            "PT_CHANNEL_#112",
            AnalogChannelType.O,
            AnalogChannelFlag.CONST,
            RecognitionResult.FAILED,
        ),
        (
            "CT_CHANNEL_#101",
            AnalogChannelType.O,
            AnalogChannelFlag.CONST,
            RecognitionResult.FAILED,
        ),
    ],
)
def test_analog_edge_cases(name, channel_type, channel_flag, result):
    detail = recognize_analog_channel(name)
    assert detail.channel_type == channel_type
    assert detail.channel_flag == channel_flag
    assert detail.result == result
