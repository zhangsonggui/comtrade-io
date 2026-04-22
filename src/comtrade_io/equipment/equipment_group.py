#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, Field

from comtrade_io.base.description import Description
from comtrade_io.channel import Analog, Status
from comtrade_io.equipment.bus import Bus
from comtrade_io.equipment.line import Line
from comtrade_io.equipment.transformer import Transformer


class EquipmentGroup(BaseModel):
    description: Description = Field(default_factory=Description, description="描述文件")
    buses: Optional[list[Bus]] = Field(default_factory=list, description="母线")
    lines: Optional[list[Line]] = Field(default_factory=list, description="线路")
    transformers: Optional[list[Transformer]] = Field(default_factory=list, description="变压器")
    analogs: Optional[dict[int, Analog]] = Field(default_factory=dict, description="模拟通道")
    statuses: Optional[dict[int, Status]] = Field(default_factory=dict, description="状态量通道")
