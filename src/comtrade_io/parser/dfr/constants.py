#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DFR 格式常量和设备注册表。"""

WNDR_TEXT_SIZE = 4088
DATA_MARKER = b"[Data]\r\n"
DEFAULT_FULL_SCALE = 32768
DEFAULT_SAMPLES_PER_CYCLE = 24
DEFAULT_GRID_FREQ = 50.0

# 已知设备注册表：device_id → 头部信息
# header_size 是设备标识行之后到第一个数据帧之间的字节数
KNOWN_DEVICES = {
    "2704V042": {"header_size": 248, "manufacturer": "ЭКРА", "model": "БЭ2704"},
    "2704V072": {"header_size": 248, "manufacturer": "ЭКРА", "model": "БЭ2704"},
}

DEFAULT_HEADER_SIZE = 0


def calc_frame_params(analog_count: int, status_count: int) -> dict:
    """根据通道数计算帧参数。

    DFR 帧结构：模拟通道（int16 LE）+ 状态字（uint16 LE），不包含序号和时间戳。

    Args:
        analog_count: 模拟通道数
        status_count: 数字通道数

    Returns:
        {"frame_size": 帧字节数, "analog_words": 模拟字数量, "status_word_count": 状态字数量}
    """
    status_word_count = (status_count + 15) // 16
    analog_words = analog_count
    frame_size = analog_words * 2 + status_word_count * 2
    return {
        "frame_size": frame_size,
        "analog_words": analog_words,
        "status_word_count": status_word_count,
    }


# 西里尔字母 → 拉丁字母转换表
CYRILLIC_TO_LATIN = str.maketrans(
    {
        "А": "A",
        "к": "k",
        "В": "V",
        "о": "o",
        "е": "e",
    }
)
