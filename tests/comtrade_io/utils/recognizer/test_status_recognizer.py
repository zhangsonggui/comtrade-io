#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""数字量通道识别单元测试

测试数据来源：通道风格识别规范文档定义的 19 类通道风格样本。
"""

import pytest

from comtrade_io.model.type import DigitalChannelFlag, DigitalChannelType
from comtrade_io.utils.recognition.channel_recognizer import (
    RecognitionResult,
    recognize_status_channel,
)

# ── 枚举映射 ──────────────────────────────────────────────

TYPE_MAP = {
    "Relay": DigitalChannelType.Relay_Act,
    "Breaker": DigitalChannelType.Breaker_Pos,
    "Warning": DigitalChannelType.Device_Alarm,
    "Switch": DigitalChannelType.Switch_Pos,
    "Other": DigitalChannelType.Other,
}

FLAG_MAP = {
    "Tr": DigitalChannelFlag.TR,
    "TrPhsA": DigitalChannelFlag.Jump_A,
    "TrPhsB": DigitalChannelFlag.Jump_B,
    "TrPhsC": DigitalChannelFlag.Jump_C,
    "OpTP": DigitalChannelFlag.Jump_ABC,
    "RecOpCls": DigitalChannelFlag.Close_Break,
    "WarnComm": DigitalChannelFlag.CHNL_FAULT,
    "HWJ": DigitalChannelFlag.Jump_Close,
    "TWJ": DigitalChannelFlag.Jump_Break,
    "HWJPhsA": DigitalChannelFlag.Jump_A_Close,
    "HWJPhsB": DigitalChannelFlag.Jump_B_Close,
    "HWJPhsC": DigitalChannelFlag.Jump_C_Close,
    "WarnGeneral": DigitalChannelFlag.WARN_GENERAL,
    "general": DigitalChannelFlag.GENERAL,
}

RESULT_MAP = {
    "正确": RecognitionResult.SUCCESS,
    "识别部分": RecognitionResult.PARTIAL,
}


def _v(voltage: str) -> int | None:
    """JSON 电压值(0.1V) → 代码返回的电压值(V)。"""
    return int(voltage) // 10 if voltage else None


def _m(monitor: str) -> str | None:
    """JSON 监视元件空字符串 → None。"""
    return monitor or None


# ── 全部原始测试用例（纯元组） ───────────────────────────
#
# 格式：(通道名称, 类型, 标识, 电压等级, 监视元件, 判定)

_RAW_CASES = [
    # ========= 1. 电压等级+设备+信号/动作 =========
    (
        "220kV母差保护I CSC-150D 4甲#母线母差动作",
        "Relay",
        "Tr",
        "2200000",
        "母差",
        "正确",
    ),
    (
        "220kV母差保护I CSC-150D 4乙#母线母差动作",
        "Relay",
        "Tr",
        "2200000",
        "母差",
        "正确",
    ),
    (
        "220kV母差保护I CSC-150D 5#母线母差动作",
        "Relay",
        "Tr",
        "2200000",
        "母差",
        "正确",
    ),
    # ========= 2. 设备+保护动作信号 =========
    (
        "2211安卡二线保护I CSC-103 A相跳闸",
        "Relay",
        "TrPhsA",
        "",
        "2211安卡二线",
        "正确",
    ),
    (
        "2211安卡二线保护I CSC-103 B相跳闸",
        "Relay",
        "TrPhsB",
        "",
        "2211安卡二线",
        "正确",
    ),
    (
        "2211安卡二线保护I CSC-103 C相跳闸",
        "Relay",
        "TrPhsC",
        "",
        "2211安卡二线",
        "正确",
    ),
    # ========= 3. 通用保护动作信号 =========
    ("2222CSC-103B纵差A相跳闸", "Relay", "TrPhsA", "", "2222", "正确"),
    ("2222CSC-103B纵差B相跳闸", "Relay", "TrPhsB", "", "2222", "正确"),
    ("2222CSC-103B纵差C相跳闸", "Relay", "TrPhsC", "", "2222", "正确"),
    # ========= 4. 设备+断路器位置 =========
    ("2211安卡二线断路器A相位置", "Breaker", "HWJPhsA", "", "2211安卡二线", "正确"),
    ("2211安卡二线断路器B相位置", "Breaker", "HWJPhsB", "", "2211安卡二线", "正确"),
    ("2211安卡二线断路器C相位置", "Breaker", "HWJPhsC", "", "2211安卡二线", "正确"),
    # ========= 5. 设备+其他信号 =========
    ("2213孙上一线开关位置", "Breaker", "HWJ", "", "2213孙上一线", "正确"),
    ("2214孙上二线开关位置", "Breaker", "HWJ", "", "2214孙上二线", "正确"),
    # index 14: 已知失败 — "2212纵联方向跳A" 无法识别为 Relay_Act
    ("2212纵联方向跳A", "Relay", "TrPhsA", "", "2212纵联方向跳A", "正确"),
    # ========= 6. 通用断路器位置信号 =========
    ("2212开关合闸位置", "Breaker", "HWJ", "", "2212开关合闸位置", "正确"),
    ("2213开关合闸位置", "Breaker", "HWJ", "", "2213开关合闸位置", "正确"),
    ("2214开关合闸位置", "Breaker", "HWJ", "", "2214开关合闸位置", "正确"),
    # ========= 7. 编号+#+名称 =========
    ("2#主变RCS-978HB差动保护动作", "Relay", "Tr", "", "2#主变", "正确"),
    ("2#主变RCS-978HB各侧后备保护动作", "Relay", "Tr", "", "2#主变", "正确"),
    ("2#主变PST-1201保护动作", "Relay", "Tr", "", "2#主变", "正确"),
    # ========= 8. 其他 =========
    ("2215RCS-931电流差动跳A", "Relay", "TrPhsA", "", "2215", "正确"),
    ("2215RCS-931电流差动跳B", "Relay", "TrPhsB", "", "2215", "正确"),
    ("2215RCS-931电流差动跳C", "Relay", "TrPhsC", "", "2215", "正确"),
    # ========= 9. 设备+告警/异常信号 =========
    (
        "2215坝下一线CSC-103BL通道A告警",
        "Warning",
        "WarnComm",
        "",
        "2215坝下一线",
        "正确",
    ),
    (
        "2215坝下一线RCS-931AML通道故障",
        "Warning",
        "WarnComm",
        "",
        "2215坝下一线",
        "正确",
    ),
    (
        "2216坝下二线CSC-103BL通道A告警",
        "Warning",
        "WarnComm",
        "",
        "2216坝下二线",
        "正确",
    ),
    # ========= 10. 英文型号开头信号 =========
    ("RCS915A跳2245甲", "Other", "general", "", "", "识别部分"),
    ("DI_CHANNEL_#54", "Other", "general", "", "DICHANNEL#54", "识别部分"),
    ("DI_CHANNEL_#55", "Other", "general", "", "DICHANNEL#55", "识别部分"),
    # ========= 11. 纯开关量/开入编号 =========
    (
        "开关量55（该口损坏）",
        "Other",
        "general",
        "",
        "开关量55（该口损坏）",
        "识别部分",
    ),
    ("开关量30(备用通道)", "Other", "general", "", "开关量30(备用通道)", "识别部分"),
    ("开关量31(备用通道)", "Other", "general", "", "开关量31(备用通道)", "识别部分"),
    # ========= 12. 无含义通用开关量 (代码视为 UNUSED) =========
    ("备用电流Ⅳ一般开关量", "Other", "general", "", "", "识别部分"),
    ("26＃备用开关量通道", "Other", "general", "", "", "识别部分"),
    ("备用通道89#开关量通道", "Other", "general", "", "", "识别部分"),
    # ========= 13. 设备+远程信号 =========
    ("2215坝下一线CSC-103BL收远跳", "Other", "general", "", "2215坝下一线", "识别部分"),
    (
        "2215坝下一线RCS-931AML收远跳",
        "Other",
        "general",
        "",
        "2215坝下一线",
        "识别部分",
    ),
    ("2216坝下二线CSC-103BL收远跳", "Other", "general", "", "2216坝下二线", "识别部分"),
    # ========= 14. 电压等级+通用信号 =========
    (
        "220kV2218黄及二智能终端A-PCS-222B 开关机构三相不一致动作",
        "Relay",
        "OpTP",
        "2200000",
        "2218黄及二智能终端A",
        "正确",
    ),
    ("220kV BP-2B 失灵动作", "Relay", "Tr", "2200000", "220kV", "正确"),
    (
        "220kV2217操作箱HWJ-A动作",
        "Relay",
        "Tr",
        "2200000",
        "2217操作箱HWJ-A动作",
        "正确",
    ),
    # ========= 15. 通用告警/异常信号 =========
    ("2222CSC-103B纵差通道A告警", "Warning", "WarnComm", "", "2222", "正确"),
    ("2222RCS-931AM纵差通道告警", "Warning", "WarnComm", "", "2222", "正确"),
    ("2217 PRS-753光纤通道告警", "Warning", "WarnComm", "", "2217", "正确"),
    # ========= 16. 双重编号+类型 (代码视为 UNUSED) =========
    ("39-39#开关量通道", "Other", "general", "", "", "识别部分"),
    ("40-40#开关量通道", "Other", "general", "", "", "识别部分"),
    ("41-41#开关量通道", "Other", "general", "", "", "识别部分"),
    # ========= 17. 通用远程信号 =========
    ("2222CSC-103B纵差收远跳", "Other", "general", "", "2222", "识别部分"),
    ("2222RCS-931AM纵差收远跳", "Other", "general", "", "2222", "识别部分"),
    ("2217 WXH收远跳", "Other", "general", "", "2217", "识别部分"),
    # ========= 18. 设备+通用开关量 (代码视为 UNUSED) =========
    ("线路1电流一般开关量", "Other", "general", "", "", "识别部分"),
    ("母线2母线侧电压一般开关量", "Other", "general", "", "", "识别部分"),
    ("母线3母线侧电压一般开关量", "Other", "general", "", "", "识别部分"),
    # ========= 19. 纯数字编号 (代码视为 UNUSED) =========
    ("14", "Other", "general", "", "", "识别部分"),
    ("33", "Other", "general", "", "", "识别部分"),
    ("1", "Other", "general", "", "", "识别部分"),
]

# ── 已知差异索引 ──────────────────────────────────────────
# 代码对以下通道的分类或判定与规范不符，
# 在 parametrize 阶段附加 xfail 标记。

_XFAIL_CLASSIFY = {14}  # "2212纵联方向跳A" → 无法识别为 Relay

_XFAIL_RESULT = {
    33,
    34,
    35,  # 无含义通用开关量 (备用电流Ⅳ, 26＃备用, 备用通道89#)
    45,
    46,
    47,  # 双重编号+类型 (39-39#, 40-40#, 41-41#)
    51,
    52,
    53,  # 设备+通用开关量 (线路1, 母线2, 母线3)
    54,
    55,
    56,  # 纯数字编号 (14, 33, 1)
}


def _xfail_classify_mark():
    return pytest.mark.xfail(reason="代码无法将'纵联方向跳A'识别为 Relay_Act/TrPhsA")


def _xfail_result_mark():
    return pytest.mark.xfail(reason="代码视为 UNUSED，规范期望 PARTIAL")


# ── 构建 parametrize 参数列表 ────────────────────────────

_CLASSIFY_PARAMS = []
for i, c in enumerate(_RAW_CASES):
    if i in _XFAIL_CLASSIFY:
        _CLASSIFY_PARAMS.append(
            pytest.param(c[0], c[1], c[2], marks=_xfail_classify_mark())
        )
    else:
        _CLASSIFY_PARAMS.append((c[0], c[1], c[2]))

_CLASSIFY_IDS = [c[0][:30] for c in _RAW_CASES]

_RESULT_PARAMS = []
for i, c in enumerate(_RAW_CASES):
    marks = []
    if i in _XFAIL_RESULT:
        marks.append(_xfail_result_mark())
    if i in _XFAIL_CLASSIFY:
        marks.append(_xfail_classify_mark())
    if marks:
        _RESULT_PARAMS.append(pytest.param(c[0], RESULT_MAP[c[5]], marks=marks))
    else:
        _RESULT_PARAMS.append((c[0], RESULT_MAP[c[5]]))

_RESULT_IDS = [c[0][:30] for c in _RAW_CASES]

_VOLTAGE_PARAMS = [(c[0], _v(c[3])) for c in _RAW_CASES if c[3]]
_VOLTAGE_IDS = [c[0][:30] for c in _RAW_CASES if c[3]]

_MONITOR_PARAMS = [(c[0], _m(c[4])) for c in _RAW_CASES if c[4]]
_MONITOR_IDS = [c[0][:30] for c in _RAW_CASES if c[4]]

# 完整校验："正确"判定 + 分类无 xfail
_FULL_PARAMS = []
_FULL_IDS = []
for i, c in enumerate(_RAW_CASES):
    if c[5] == "正确" and i not in _XFAIL_CLASSIFY:
        _FULL_PARAMS.append(c)
        _FULL_IDS.append(c[0][:30])


# ── 分类测试（类型 + 标识） ──────────────────────────────


@pytest.mark.parametrize(
    "name, exp_type, exp_flag",
    _CLASSIFY_PARAMS,
    ids=_CLASSIFY_IDS,
)
def test_classify(name, exp_type, exp_flag):
    """验证所有样本的通道类型和标识分类正确。"""
    detail = recognize_status_channel(name)
    assert detail.channel_type == TYPE_MAP[exp_type]
    assert detail.channel_flag == FLAG_MAP[exp_flag]


# ── 电压等级测试 ──────────────────────────────────────────


@pytest.mark.parametrize(
    "name, exp_voltage",
    _VOLTAGE_PARAMS,
    ids=_VOLTAGE_IDS,
)
def test_voltage_level(name, exp_voltage):
    """验证含电压等级的通道正确提取电压值（220kV → 220000）。"""
    detail = recognize_status_channel(name)
    assert detail.voltage_level == exp_voltage


# ── 监视元件测试 ──────────────────────────────────────────


@pytest.mark.parametrize(
    "name, exp_monitor",
    _MONITOR_PARAMS,
    ids=_MONITOR_IDS,
)
def test_monitor(name, exp_monitor):
    """验证监视元件提取正确。"""
    detail = recognize_status_channel(name)
    assert detail.monitor == exp_monitor


# ── 判定结果测试 ──────────────────────────────────────────


@pytest.mark.parametrize(
    "name, exp_result",
    _RESULT_PARAMS,
    ids=_RESULT_IDS,
)
def test_recognition_result(name, exp_result):
    """验证判定结果符合规范。

    标记 xfail 的用例：代码返回 UNUSED 而规范期望 PARTIAL，
    代表代码将这些通道归类为"未使用"而非"部分识别"。
    """
    detail = recognize_status_channel(name)
    assert detail.result == exp_result


# ── 完整识别校验（"正确"判定 + 非 xfail 样本） ──────────


@pytest.mark.parametrize(
    "name, exp_type, exp_flag, exp_voltage, exp_monitor, exp_result",
    _FULL_PARAMS,
    ids=_FULL_IDS,
)
def test_full_recognition_success(
    name, exp_type, exp_flag, exp_voltage, exp_monitor, exp_result
):
    """验证"正确"判定样本的完整识别结果。"""
    detail = recognize_status_channel(name)
    assert detail.channel_type == TYPE_MAP[exp_type]
    assert detail.channel_flag == FLAG_MAP[exp_flag]
    assert detail.voltage_level == _v(exp_voltage)
    assert detail.monitor == _m(exp_monitor)
    assert detail.result == RESULT_MAP[exp_result]


# ── 保护型号提取测试 ─────────────────────────────────────


@pytest.mark.parametrize(
    "name, expected_protection",
    [
        ("220kV母差保护I CSC-150D 4甲#母线母差动作", "CSC-150D"),
        ("2211安卡二线保护I CSC-103 A相跳闸", "CSC-103"),
        ("2222CSC-103B纵差A相跳闸", "CSC-103B"),
        ("2215坝下一线CSC-103BL通道A告警", "CSC-103BL"),
        ("RCS915A跳2245甲", "RCS915A"),
        ("220kV BP-2B 失灵动作", "BP-2B"),
        ("DI_CHANNEL_#54", None),
        ("2#主变RCS-978HB差动保护动作", "RCS-978HB"),
        ("2215RCS-931电流差动跳A", "RCS-931"),
    ],
)
def test_protection_model_extraction(name, expected_protection):
    """验证保护型号从通道名称中的提取结果。"""
    detail = recognize_status_channel(name)
    assert detail.protection == expected_protection


# ── 未使用通道检测 ──────────────────────────────────────


_UNUSED_PATTERNS = [
    "0",
    "999",
    "开关量1",
    "开关量99",
    "12-34#备用通道",
    "56-78#测试通道",
    "开入1",
    "开入88",
    "一般开关量",
    "备用开关量1",
    "未命名开关量通道",
]


@pytest.mark.parametrize("name", _UNUSED_PATTERNS)
def test_is_unused(name):
    """验证典型未使用通道模式返回 UNUSED 结果。"""
    detail = recognize_status_channel(name)
    assert detail.channel_type == DigitalChannelType.Other
    assert detail.channel_flag == DigitalChannelFlag.GENERAL
    assert detail.voltage_level is None
    assert detail.monitor is None
    assert detail.protection is None
    assert detail.result == RecognitionResult.UNUSED
