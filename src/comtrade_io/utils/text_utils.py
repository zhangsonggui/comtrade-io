#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文本分割工具
支持按分隔符分割单行或多行文本
"""


def text_split(
        string: str,
        split_char: str = ',',
        strip: bool = True,
        filter_empty: bool = True
) -> list[str]:
    """
    文本分割函数
    - 支持单行按 split_char 分割
    - 支持多行文本：按行分割后再按 split_char 分割，结果展平拼接
    - 空字符串或不包含分割字符时返回空列表而非抛异常

    :param string: 要分割的字符串
    :param split_char: 分隔符，默认逗号
    :param strip: 是否去除元素首尾空白，默认 True
    :param filter_empty: 是否过滤空元素，默认 True
    :return: 分割后的字符串列表
    """
    if string is None:
        string = ""

    _str = str(string)

    # 统一处理换行符
    if '\n' in _str or '\r' in _str:
        _norm = _str.replace('\r\n', '\n').replace('\r', '\n')
        lines = _norm.split('\n')
    else:
        lines = [_str]

    result = []
    for line in lines:
        if split_char in line:
            parts = line.split(split_char)
        else:
            parts = [line]

        for part in parts:
            if strip:
                part = part.strip()
            if filter_empty and not part:
                continue
            result.append(part)

    return result
