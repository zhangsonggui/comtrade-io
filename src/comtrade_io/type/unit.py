#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class Multiplier(BaseEnum):
    """单位乘数枚举

    定义标准SI单位前缀。
    """
    T = ('T', 1e12, "太")
    G = ('G', 1e9, "吉")
    M = ('M', 1e6, "兆")
    k = ('k', 1e3, "千")
    NONE = ('', 1.0, "无")
    m = ('m', 1e-3, "毫")
    u = ('μ', 1e-6, "微")
    n = ('n', 1e-9, "纳")
    p = ('p', 1e-12, "皮")

    @property
    def multiplier_value(self) -> float:
        if isinstance(self._value_, tuple) and len(self._value_) > 1:
            try:
                return float(self._value_[1])
            except (ValueError, TypeError):
                return 1.0
        return 1.0


class BaseUnit(BaseEnum):
    """基本单位枚举

    定义电力系统中常用的物理量基本单位。
    """
    V = ('V', "伏特")
    A = ('A', "安培")
    Hz = ('Hz', "赫兹")
    Ohm = ('Ω', "欧姆")
    W = ('W', "瓦特")
    Var = ('Var', "乏")
    NONE = ('', "无")


class Unit(BaseEnum):
    """单位枚举（兼容模式）

    兼容解析合并格式如 kV、mA，同时也支持分离解析。
    """
    V = ('V', BaseUnit.V, 1.0)
    mV = ('mV', BaseUnit.V, 1e-3)
    kV = ('kV', BaseUnit.V, 1e3)
    A = ('A', BaseUnit.A, 1.0)
    mA = ('mA', BaseUnit.A, 1e-3)
    kA = ('kA', BaseUnit.A, 1e3)
    Hz = ('Hz', BaseUnit.Hz, 1.0)
    kHz = ('kHz', BaseUnit.Hz, 1e3)
    MHz = ('MHz', BaseUnit.Hz, 1e6)
    Ohm = ('Ω', BaseUnit.Ohm, 1.0)
    kOhm = ('kΩ', BaseUnit.Ohm, 1e3)
    MOhm = ('MΩ', BaseUnit.Ohm, 1e6)
    W = ('W', BaseUnit.W, 1.0)
    kW = ('kW', BaseUnit.W, 1e3)
    MW = ('MW', BaseUnit.W, 1e6)
    Var = ('Var', BaseUnit.Var, 1.0)
    kVar = ('kVar', BaseUnit.Var, 1e3)
    MVar = ('MVar', BaseUnit.Var, 1e6)
    NONE = ('', BaseUnit.NONE, 1.0)

    @property
    def base_unit(self) -> BaseUnit:
        if isinstance(self._value_, tuple) and len(self._value_) > 1:
            return self._value_[1]
        return BaseUnit.NONE

    @property
    def multiplier_value(self) -> float:
        if isinstance(self._value_, tuple) and len(self._value_) > 2:
            return self._value_[2]
        return 1.0

    @property
    def multiplier(self) -> Multiplier:
        val = self.multiplier_value
        for m in Multiplier:
            if m.multiplier_value == val:
                return m
        return Multiplier.NONE
