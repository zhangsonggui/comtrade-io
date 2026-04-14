#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base_enum import BaseEnum


class TranSide(BaseEnum):
    """转换标识枚举

    定义是一次侧还是二次侧的转换标识。
    """
    P = ("P", "一次侧")
    S = ("S", "二次侧")
