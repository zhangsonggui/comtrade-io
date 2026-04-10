#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
    anas: list[Analog] = Field(default_factory=list, description="模拟通道")
    stas: list[Status] = Field(default_factory=list, description="开关量通道")
