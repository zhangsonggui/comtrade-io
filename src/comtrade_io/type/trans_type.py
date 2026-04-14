#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class TransWindLocation(BaseEnum):
    """变压器绕组位置枚举

    定义变压器绕组在变压器中的位置。
    """
    HIGH = ("high", "高压侧")
    MEDIUM = ("medium", "中压侧")
    LOW = ("low", "低压侧")
    COMMON = ("common", "公共绕组")


class WindFlag(BaseEnum):
    """变压器绕组连接方式枚举

    定义变压器绕组的连接方式。
    """
    Y = ('y', "星形连接")
    YN = ('yn', "星形接地")
    D = ('d', "三角形连接")
    Z = ('z', "曲折型连接")
