#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class TransWindLocation(BaseEnum):
    HIGH = ("high", "高压侧")
    MEDIUM = ("medium", "中压侧")
    LOW = ("low", "低压侧")
    COMMON = ("common", "公共绕组")


class WindFlag(BaseEnum):
    Y = ('y', "星形")
    YN = ('yn', "星形接地")
    D = ('d', "三角形")
