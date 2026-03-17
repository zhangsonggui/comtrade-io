#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class TvInstallSite(BaseEnum):
    BUS = ("BUS", "母线侧")
    LINE = ("LINE", "线路侧")
