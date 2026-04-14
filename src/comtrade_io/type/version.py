#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.type.base_enum import BaseEnum


class Version(BaseEnum):
    """COMTRADE版本枚举

    定义支持的COMTRADE标准版本。
    """
    V1991 = ('1991', "IEEE Std C37.111-1991")
    V1999 = ('1999', "IEEE Std C37.111-1999")
    V2001 = ('2001', "IEEE 60255-24:2001")
    V2008 = ('2008', "GB/T 22386-2008")
    V2013 = ('2013', "IEEE 60255-24:2013")
    V2017 = ('2017', "GB/T 14598.24-2017")
