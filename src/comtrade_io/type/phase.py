#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class Phase(BaseEnum):
    """相别枚举

    定义电力系统中的相别类型，包括A相、B相、C相、N相（中性线）和L相（相线）。
    """
    PHASE_A = ("A", "A相")
    PHASE_B = ("B", "B相")
    PHASE_C = ("C", "C相")
    PHASE_N = ("N", "N相")
    PHASE_L = ("L", "L相")
    NONE = ("", "无")
