#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class Unit(BaseEnum):
    V = ('V', "伏特")
    A = ('A', "安培")
    kV = ('kV', "千伏")
    kA = ('kA', "千安")
    Hz = ('Hz', "赫兹")
    Ohm = ('Ω', "欧姆")
    W = ('W', "瓦特")
    Var = ('Var', "乏")
    NONE = ('', "无")
