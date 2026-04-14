#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class CurrentBranchNum(BaseEnum):
    """电流分支数量枚举

    定义线路电流分支的数量模式。
    """
    B1 = (1, "普通线路或3/2接线和电流模式")
    B2 = (2, "2/3接线分电流模式")
