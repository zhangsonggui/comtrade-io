#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.type.base_enum import BaseEnum


class Contact(BaseEnum):
    """触点类型枚举

    定义继电器或开关触点的正常状态类型。
    """
    NormallyOpen = ("0", "常开")
    NormallyClosed = ("1", "常闭")
