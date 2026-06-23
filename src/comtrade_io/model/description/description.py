#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import datetime

from pydantic import Field

from comtrade_io.model.description.channel_num import ChannelNum
from comtrade_io.model.description.header import Header
from comtrade_io.model.description.index_base import ReferenceBaseModel
from comtrade_io.model.description.sampling import Sampling
from comtrade_io.model.description.sampling_time_quality import SamplingTimeQuality
from comtrade_io.model.description.time_info import TimeInfo
from comtrade_io.model.type import DataType


class Description(ReferenceBaseModel):
    """描述文件模型"""

    xmlns_scl: str = Field(
        default="http://www.iec.ch/61850/2003/SCL", description="XML命名空间"
    )
    xmlns_xsi: str = Field(
        default="http://www.w3.org/2001/XMLSchema-instance", description="XML命名空间"
    )
    data_model_version: float = Field(default=1.0, description="数据模型版本")
    xsi_schema_location: str = Field(
        default="http://www.iec.ch/61850/2003/SCLcomtrade_mdl_v1.1.xsd",
        description="XML架构",
    )
    header: Header | None = Field(default_factory=Header, description="文件头")
    channel_num: ChannelNum | None = Field(
        default_factory=lambda: ChannelNum(total=0, analog=0, status=0),
        description="通道数量",
    )
    sampling: Sampling | None = Field(default_factory=Sampling, description="采样信息")
    file_start_time: datetime | None = Field(
        default_factory=datetime.now, description="文件开始时间"
    )
    trigger_time: datetime | None = Field(
        default_factory=datetime.now, description="触发时间"
    )
    data_type: DataType | None = Field(default=DataType.BINARY, description="数据格式")
    timemult: float | None = Field(default=1.0, description="时标倍率因子")
    time_info: TimeInfo | None = Field(
        default_factory=TimeInfo, description="时间信息及与UTC时间关系"
    )
    sampling_time_quality: SamplingTimeQuality | None = Field(
        default_factory=SamplingTimeQuality, description="采样时间品质"
    )

    @property
    def station_name(self) -> str:
        """向后兼容：委托到 header.station"""
        return self.header.station if self.header else ""

    @station_name.setter
    def station_name(self, value: str):
        if self.header is None:
            self.header = Header(station=value)
        else:
            self.header.station = value

    @property
    def rec_dev_name(self) -> str:
        """向后兼容：委托到 header.recorder"""
        return self.header.recorder if self.header else ""

    @rec_dev_name.setter
    def rec_dev_name(self, value: str):
        if self.header is None:
            self.header = Header(recorder=value)
        else:
            self.header.recorder = value

    @property
    def version(self):
        """向后兼容：委托到 header.version"""
        return self.header.version if self.header else None

    @version.setter
    def version(self, value):
        if self.header is None:
            from comtrade_io.model.type import Version

            self.header = Header(
                version=Version(value) if isinstance(value, int) else value
            )
        else:
            self.header.version = value

    def to_dmf(self):
        attrs = [
            f'xmlns:scl="{self.xmlns_scl}"',
            f'xmlns:xsi="{self.xmlns_xsi}"',
            f'stationName="{self.header.station}"',
            f'version="{self.header.version.value}"',
            f'recDevName="{self.header.recorder}"',
            f'xsi:schemaLocation="{self.xsi_schema_location}"',
        ]
        xml = f'<?xml version="1.0" encoding="UTF-8"?>'
        xml += "\n" + f'<scl:ComtradeModel {" ".join(attrs)}>'
        return xml

    def to_inf(self) -> str:
        from comtrade_io.parser.description.date_time_parser import (
            format_datetime_for_cfg,
        )

        attrs = [
            f"[Public File_Description]",
            self.header.to_inf(),
            self.channel_num.to_inf(),
            self.sampling.to_inf(),
            f"File_Start_Time={format_datetime_for_cfg(self.file_start_time) if self.file_start_time else ''}",
            f"Trigger_Time={format_datetime_for_cfg(self.trigger_time) if self.trigger_time else ''}",
            f"File_Type={self.data_type.value}",
            f"Time_Multiplier={self.timemult}",
        ]
        return "\n".join(attrs)
