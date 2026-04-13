#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from comtrade_io.channel import Analog, Status
from comtrade_io.equipment.equipment import Equipment


def parse_number_with_unit(s: str) -> float:
    match = re.search(r'\d+\.?\d*', s)
    return float(match.group()) if match else 0.0


def parse_four_values(s: str) -> list[float]:
    parts = s.split(',')
    return [parse_number_with_unit(p) for p in parts[:4]]


def parse_two_values(s: str) -> list[float]:
    parts = s.split(',')
    return [parse_number_with_unit(p) for p in parts[:2]]


def str2ids(string: str) -> list[int] | None:
    """
    将逗号分隔的字符串转换为整数ID列表

    Args:
        string: 逗号分隔的数字字符串，例如 "1,2,3"

    Returns:
        转换后的非零整数列表，如果输入为空或包含无效数字则返回 None

    Note:
        - 自动跳过空字符串和值为0的数字
        - 遇到无法转换为整数的内容时立即返回 None
    """
    if not string or not string.strip():
        return None

    parts = string.strip().split(",")
    result = []
    for part in parts:
        part = part.strip()
        if part:  # 跳过空字符串
            try:
                _id = int(part)
                if _id != 0:
                    if not result or _id > result[-1]:
                        result.append(_id)
            except ValueError:
                # 遇到无效数字时返回None或跳过，根据业务需求决定
                return None
    return result if result else None


def str2channel(string: str, channels: dict[int, Analog | Status]):
    ids = str2ids(string)
    return [channels.get(i) for i in ids if channels.get(i) is not None] if ids else []


class EquipmentSection:
    """部件基类"""

    @classmethod
    def from_dict(cls,
                  data: dict,
                  analog_channels: dict[int, Analog],
                  status_channels: dict[int, Status]) -> Equipment:
        index = data.get("index", None)
        uuid = data.get("SYS_ID", "")
        name_str = data.get('DEV_ID', data.get('Name', ''))
        if ',' in name_str:
            _, name = name_str.split(',', 1)
        else:
            name = name_str
        if not name:
            name = f"Equipment_{index if index else 0}"
        voltages = str2channel(data.get("TV_CHNS", ""), analog_channels)
        currents = str2channel(data.get("TA_CHNS", ""), analog_channels)
        stas = str2channel(data.get("STATUS_CHNS", ""), status_channels)

        return Equipment(index=index,
                         uuid=uuid,
                         name=name,
                         acvs=voltages,
                         accs=currents,
                         stas=stas)
