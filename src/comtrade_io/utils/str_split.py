#!/usr/bin/env python
# -*- coding: utf-8 -*-


def str_split(string: str, split_char: str = ',') -> list:
    """
    字符串分割函数
    - 支持单行按 split_char 分割
    - 支持多行文本：按行分割后再按 split_char 分割，每行的分割结果会被展平拼接，保持输入顺序
    - 如果字符串为空或不包含分割字符，会抛出 ValueError
    """
    if string is None:
        raise ValueError("传入的字符串为 None")
    _str = str(string).strip()
    if _str == '':
        raise ValueError(f"传入的字符串'{_str}'为空")

    # 处理多行情况
    if '\n' in _str or '\r' in _str:
        # 兼容不同换行符，统一转换为 \n
        _norm = _str.replace('\r\n', '\n').replace('\r', '\n')
        lines = [ln for ln in _norm.split('\n') if ln != '']
        result = []
        for line in lines:
            if not line:
                continue
            if split_char in line:
                result.extend(line.split(split_char))
            else:
                # 如果该行没有分割字符，作为一个整体加入
                result.append(line)
        if not result:
            raise ValueError(f"传入的字符串'{_str}'为空或不包含分割字符({split_char})")
        return result

    # 单行情况，直接使用 split_char 进行分割
    if split_char not in _str:
        raise ValueError(f"传入的字符串'{_str}'为空或不包含分割字符({split_char})")
    return _str.split(split_char)
