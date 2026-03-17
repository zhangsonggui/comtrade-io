#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from typing import Optional

from pydantic import BaseModel, Field

from comtrade_io.type.version import Version
from comtrade_io.utils.str_split import str_split


class Header(BaseModel):
    """文件头类

    表示COMTRADE配置文件的头部信息，包含变电站名称、录波设备标识和版本号。
    字符串表示形如: "变电站,故障录波设备,1991"

    属性:
        station: 变电站名称
        recorder: 故障录波设备标识
        version: COMTRADE标准版本号
    """
    station: Optional[str] = Field(default='变电站', description="变电站")
    recorder: Optional[str] = Field(default='故障录波设备', description="故障录波设备")
    version: Optional[Version] = Field(default=Version.V1991, description="版本")

    def __str__(self):
        """序列化为逗号分隔的逗号分隔的字符串"""
        return f"{self.station},{self.recorder},{self.version.value}"

    @classmethod
    def from_str(cls, _str: str) -> 'Header':
        """从逗号分隔的字符串反序列化文件头

        将包含变电站名称、录波设备和版本号的字符串解析为Header对象。

        参数:
            _str: 逗号分隔的文件头字符串，如 "变电站,录波器,1991"

        返回:
            Header: 解析后的文件头对象
        """
        str_arr = str_split(_str)
        if len(str_arr) < 2:
            return cls()
        if len(str_arr) < 3:
            return cls(station=str_arr[0], recorder=str_arr[1], version=Version.V1991)
        return cls(station=str_arr[0], recorder=str_arr[1], version=Version.from_value(str_arr[2], Version.V1991))

    @classmethod
    def from_dict(cls, data: dict) -> 'Header':
        """从字典反序列化"""
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Header':
        """从JSON字符串反序列化"""
        data = json.loads(json_str)
        return cls.from_dict(data)
