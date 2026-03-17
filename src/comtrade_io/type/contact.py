#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.type.base_enum import BaseEnum


class Contact(BaseEnum):
    NormallyOpen = ("0", "常开")
    NormallyClosed = ("1", "常闭")
