#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.type.base_enum import BaseEnum


class DataType(BaseEnum):
    """数据格式类型枚举

    定义COMTRADE数据文件的存储格式类型。
    """
    ASCII = ("ASCII", "ASCII编码")
    BINARY = ("BINARY", "二进制")
    BINARY32 = ("BINARY32", "32位二进制")
    FLOAT32 = ("FLOAT32", "32位浮点")
