#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field

from comtrade_io.model.type.version import Version


class Header(BaseModel):
    """文件头类

    表示COMTRADE配置文件的头部信息，包含变电站名称、录波设备标识和版本号。
    字符串表示形如: "变电站,故障录波设备,1991"

    属性:
        station: 变电站名称
        recorder: 故障录波设备标识
        version: COMTRADE标准版本号
    """

    station: str | None = Field(default="变电站", description="变电站")
    recorder: str | None = Field(default="故障录波设备", description="故障录波设备")
    version: Version | None = Field(default=Version.V1991, description="版本")

    def __str__(self):
        """序列化为逗号分隔的逗号分隔的字符串"""
        return f"{self.station},{self.recorder},{self.version.value}"

    def to_inf(self) -> str:
        """
        将描述文件转换为INF格式字符串

        返回:
            INF格式字符串
        """
        attrs = [
            f"Station_Name={self.station}",
            f"Recording_Device_ID={self.recorder}",
            f"Revision_Year={self.version.value}",
        ]
        return "\n".join(attrs)
