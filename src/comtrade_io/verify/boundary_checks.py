#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""边界检查工具模块"""
from typing import Union


def check_index_range(
        index: int,
        min_value: int,
        max_value: int,
        raise_error: bool = True
) -> bool:
    """
    检查索引是否在有效范围内

    参数:
        index: 要检查的索引值
        min_value: 最小允许值（包含）
        max_value: 最大允许值（包含）
        raise_error: 是否在超出范围时抛出异常

    返回:
        bool: 索引是否在范围内
    """
    if min_value <= index <= max_value:
        return True
    if raise_error:
        raise IndexError(f"索引值应在[{min_value}, {max_value}]之间，输入的: {index}超出范围")
    return False


def check_positive(value: Union[int, float], allow_zero: bool = False) -> bool:
    """
    检查值是否为正数

    参数:
        value: 要检查的值
        allow_zero: 是否允许零值

    返回:
        bool: 值是否有效
    """
    if allow_zero:
        return value >= 0
    return value > 0


def check_not_empty(value: str, field_name: str = "字段") -> bool:
    """
    检查字符串是否非空

    参数:
        value: 要检查的字符串
        field_name: 字段名称（用于错误消息）

    返回:
        bool: 字符串是否非空
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name}不能为空")
    return True


def clamp(value: Union[int, float], min_value: Union[int, float], max_value: Union[int, float]) -> Union[int, float]:
    """
    将值限制在指定范围内

    参数:
        value: 要限制的值
        min_value: 最小值
        max_value: 最大值

    返回:
        Union[int, float]: 限制后的值
    """
    return max(min_value, min(value, max_value))
