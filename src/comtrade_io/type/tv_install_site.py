#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class TvInstallSite(BaseEnum):
    """电压互感器安装位置枚举

    定义电压互感器(TV)的安装位置。
    """
    BUS = ("BUS", "母线侧")
    LINE = ("LINE", "线路侧")
