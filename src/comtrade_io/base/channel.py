#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import Field

from comtrade_io.base import IndexBaseModel
from comtrade_io.type import Phase


class ChannelBaseModel(IndexBaseModel):
    """
    通道基类
    参数:
        index(int): 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        name(str): 通道标识（ch_id）
        phase(Phase): 通道相别标识（ph）
    返回:
        基础通道对象ChannelBaseModel
    """
    name: Optional[str] = Field(default=None, description="通道标识")
    phase: Optional[Phase] = Field(default=Phase.NONE, description="通道相别标识")

    def __str__(self) -> str:
        """序列化为逗号分隔的通道字符串"""
        phase_value = self.phase.value if self.phase else ""
        return f"{self.index},{self.name},{phase_value}"
