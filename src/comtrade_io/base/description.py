#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import Field

from comtrade_io.base import ReferenceBaseModel
from comtrade_io.type import Version


class Description(ReferenceBaseModel):
    """描述文件模型
    """
    xmlns_scl: str = Field(default="http://www.iec.ch/61850/2003/SCL", description="XML命名空间")
    xmlns_xsi: str = Field(default="http://www.w3.org/2001/XMLSchema-instance", description="XML命名空间")
    station_name: str = Field(default="", description="站点名称")
    data_model_version: float = Field(default=1.0, description="数据模型版本")
    rec_dev_name: str = Field(default="", description="录波设备")
    version: Optional[Version] = Field(default=Version.V1991, description="版本")
    xsi_schema_location: str = Field(default="http://www.iec.ch/61850/2003/SCLcomtrade_mdl_v1.1.xsd",
                                     description="XML架构")

    def __str__(self):
        """
        返回COMTRADE模型XML根元素的字符串表示

        返回:
            格式化的XML字符串，包含XML声明和根元素开始标签
        """
        attrs = [
            f'xmlns:scl="{self.xmlns_scl}"',
            f'xmlns:xsi="{self.xmlns_xsi}"',
            f'stationName="{self.station_name}"',
            f'version="{self.data_model_version}"',
            f'recDevName="{self.rec_dev_name}"',
            f'xsi:schemaLocation="{self.xsi_schema_location}"'
        ]
        xml = f'<?xml version="1.0" encoding="UTF-8"?>'
        xml += "\n" + f'<scl:ComtradeModel {" ".join(attrs)}>'
        return xml

    def to_inf(self) -> str:
        """
        将描述文件转换为INF格式字符串

        返回:
            INF格式字符串
        """
        attrs = [
            f"[Public File_Description]",
            f"Station_Name={self.station_name}",
            f"Recording_Device_ID={self.rec_dev_name}",
            f"Revision_Year={self.version.value}"
        ]
        return "\n".join(attrs)
