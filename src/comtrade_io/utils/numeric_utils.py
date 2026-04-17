#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据解析工具函数模块
包含通用的数据类型转换和解析功能
"""
import re
from typing import Any, Optional

_NUMERIC_PATTERN = re.compile(r'[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?')


def _convert_to_float(value: Any, default: float = 0.0, key: Optional[str] = None, strip_chars: str = ",") -> float:
    """
    内部通用浮点数转换函数

    :param value: 要转换的值
    :param default: 当值为None或空字符串时的默认值
    :param key: 可选的键名，用于错误信息
    :return: 转换后的浮点数
    :raises ValueError: 当值无法转换为浮点数时
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return default

    s = value
    if isinstance(value, str):
        s = value.strip(strip_chars).strip().replace(",", "").replace(" ", "")

    try:
        return float(s)
    except (ValueError, TypeError):
        if isinstance(value, str):
            m = _NUMERIC_PATTERN.search(value)
            if m:
                try:
                    return float(m.group(0))
                except ValueError:
                    pass
        if key is not None:
            raise ValueError(f"无法将'{key}'的值 '{value}' 转换为浮点数")
        else:
            raise ValueError(f"无法将'{value}' 转换为浮点数")


def _convert_to_int(value: Any, default: int = 0, key: Optional[str] = None) -> int:
    """
    内部通用整数转换函数

    :param value: 要转换的值
    :param default: 当值为None或空字符串时的默认值
    :param key: 可选的键名，用于错误信息
    :return: 转换后的整数
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return default

    s = value
    if isinstance(value, str):
        s = value.strip().strip(",").replace(",", "").strip()

    try:
        return int(s)
    except (ValueError, TypeError):
        try:
            return int(float(s))
        except (ValueError, TypeError):
            if key is not None:
                raise ValueError(f"无法将'{key}'的值 '{value}' 转换为整数")
            else:
                return default


def parse_float(value: Any, default: float = 0.0) -> float:
    """
    解析字符串值为浮点数，处理空字符串情况

    :param value: 要解析的字符串值
    :param default: 当值为空字符串或无法转换时的默认值
    :return: 解析后的浮点数
    """
    try:
        return _convert_to_float(value, default=default, key=None)
    except ValueError:
        return default


def parse_int(value: Any, default: int = 0) -> int:
    """
    解析字符串值为整数，处理空字符串情况

    :param value: 要解析的字符串值
    :param default: 当值为空字符串或无法转换时的默认值
    :return: 解析后的整数
    """
    try:
        return _convert_to_int(value, default=default, key=None)
    except ValueError:
        return default
