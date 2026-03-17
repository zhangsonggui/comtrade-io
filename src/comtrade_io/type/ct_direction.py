#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class CtDirection(BaseEnum):
    POS = ("pos", "正向")
    NEG = ("neg", "反向")
    UNC = ("unc", "未知")
