#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试通道识别功能
"""

import io
import sys

# 设置标准输出编码为utf-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from comtrade_io.utils.channel_recognizer import (
    recognize_channel_type,
    recognize_channel_flag,
    recognize_channel
)


def test_channel_recognition():
    """测试通道识别功能"""

    # 测试用例：通道名称 -> 预期类型, 预期标志
    test_cases = [
        # 交流电压 - 使用实际的中文字符
        ("220kV母线_Ua", "A", "ACV"),
        ("220kV母线_Ub", "A", "ACV"),
        ("220kV母线_Uc", "A", "ACV"),
        ("220kV母线_3U0", "A", "ACV"),
        ("35kV母线_Ua", "A", "ACV"),
        ("母线3 Ua", "A", "ACV"),

        # 交流电流
        ("220kV hh1x_211开关_Ia", "A", "ACC"),
        ("220kV hh1x_211开关_Ib", "A", "ACC"),
        ("220kV hh1x_211开关_Ic", "A", "ACC"),
        ("220kV hh1x_211开关_3I0", "A", "ACC"),
        ("220kV 母联_Ia", "A", "ACC"),
        ("5 Ia", "A", "ACC"),

        # 直流通道
        ("#3主变直1+", "D", "CONST"),
        ("#3主变直1-", "D", "CONST"),
        ("直2+", "D", "CONST"),
        ("直2-", "D", "CONST"),

        # 通用测试
        ("电压A相", "A", "ACV"),
        ("电流A相", "A", "ACC"),
        ("U1", "A", "ACV"),
        ("I1", "A", "ACC"),
        ("P", "A", "PW"),
        ("Q", "A", "PW"),
        ("f", "A", "FQ"),
    ]

    print("=== 通道识别功能测试 ===\n")

    passed = 0
    failed = 0

    for channel_name, expected_type, expected_flag in test_cases:
        try:
            channel_type, channel_flag = recognize_channel(channel_name)
            type_match = channel_type.get_value() == expected_type
            flag_match = channel_flag.get_value() == expected_flag

            status = "[PASS]" if type_match and flag_match else "[FAIL]"
            if type_match and flag_match:
                passed += 1
            else:
                failed += 1

            result = f"{status} {channel_name:30s} -> "
            result += f"type: {channel_type.get_value()} ({expected_type}) "
            result += f"{'OK' if type_match else 'NG'}, "
            result += f"flag: {channel_flag.get_value():4s} ({expected_flag:4s}) "
            result += f"{'OK' if flag_match else 'NG'}"
            print(result)
        except Exception as e:
            failed += 1
            print(f"[FAIL] {channel_name:30s} -> exception: {e}")

    print(f"\n=== 测试结果: {passed} 通过, {failed} 失败 ===")

    # 额外测试：单独测试识别函数
    print("\n=== 单独测试识别函数 ===")
    name = "220kV hh1x_211开关_Ia"
    print(f"通道名称: {name}")
    print(f"识别类型: {recognize_channel_type(name).get_value()}")
    print(f"识别标志: {recognize_channel_flag(name).get_value()}")


if __name__ == "__main__":
    test_channel_recognition()
