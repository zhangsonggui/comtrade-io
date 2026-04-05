#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class Phase(BaseEnum):
    PHASE_A = ("A", "A相")
    PHASE_B = ("B", "B相")
    PHASE_C = ("C", "C相")
    PHASE_N = ("N", "N相")
    PHASE_L = ("L", "L相")
    NONE = ("", "无")
