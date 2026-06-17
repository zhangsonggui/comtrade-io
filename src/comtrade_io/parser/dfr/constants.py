#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DFR 格式常量和设备注册表。"""

WNDR_TEXT_SIZE = 4088
DATA_MARKER = b"[Data]\r\n"
FRAME_SIZE = 72
ANALOG_WORDS = 32
STATUS_WORDS = 4
DEFAULT_FULL_SCALE = 32768
DEFAULT_SAMPLES_PER_CYCLE = 24
DEFAULT_GRID_FREQ = 50.0

# 已知设备注册表：device_id → 头部信息
# header_size 是设备标识行之后到第一个数据帧之间的字节数
KNOWN_DEVICES = {
    "2704V042": {"header_size": 248, "manufacturer": "ЭКРА", "model": "БЭ2704"},
}

DEFAULT_HEADER_SIZE = 0

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
