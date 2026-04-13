#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import Field

from comtrade_io.base import IndexBaseModel, ReferenceBaseModel
from comtrade_io.channel.analog import Analog
from comtrade_io.channel.status import Status


class Equipment(IndexBaseModel, ReferenceBaseModel):
    """
    设备基础类
    """
    name: str = Field(..., description="设备名称")
    uuid: str = Field(default="", description="设备标识")
    stas: list[Status] = Field(default_factory=list, description="开关量通道")
    acvs: Optional[list[Analog]] = Field(default_factory=list, description="电压通道")
    accs: Optional[list[Analog]] = Field(default_factory=list, description="电流通道")

    def _get_ana_chn_xml(self) -> str:
        """
        获取模拟量通道的XML表示

        Returns:
            str: 模拟量通道的XML字符串
        """
        xml_parts = []
        all_analogs = []
        if self.acvs:
            all_analogs.extend(self.acvs)
        if self.accs:
            all_analogs.extend(self.accs)
        for ana in all_analogs:
            if ana:
                xml_parts.append(f'\n\t\t<scl:AnalogRef idx="{ana.index}" />')
        return "".join(xml_parts)

    def _get_sta_chn_xml(self) -> str:
        """
        获取开关量通道的XML表示

        Returns:
            str: 开关量通道的XML字符串
        """
        xml_parts = []
        for sta in self.stas:
            if sta:
                xml_parts.append(f'\n\t\t<scl:StatusRef idx="{sta.index}" />')
        return "".join(xml_parts)
