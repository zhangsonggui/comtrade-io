#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, Field

from comtrade_io.channel import Analog, Status
from comtrade_io.equipment import Bus, Line, Transformer


class ComtradeModel(BaseModel):
    buses: Optional[list[Bus]] = Field(default_factory=list, description="母线")
    lines: Optional[list[Line]] = Field(default_factory=list, description="线路")
    transformers: Optional[list[Transformer]] = Field(default_factory=list, description="变压器")
    analogs: Optional[list[Analog]] = Field(default_factory=list, description="模拟通道")
    statuses: Optional[list[Status]] = Field(default_factory=list, description="状态量通道")
