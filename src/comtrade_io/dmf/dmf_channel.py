#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMF通道模块

定义DMF数据模型中的通道基类，包括模拟通道和开关量通道的通用属性。
"""

from pydantic import BaseModel, Field

from comtrade_io.type import (AnalogChannelFlag, AnalogChannelType, DigitalChannelFlag, DigitalChannelType)


class DmfChannel(BaseModel):
    """
    DMF通道基类
    
    定义模拟量和开关量通道的通用属性，包括端子排号、通道类型和通道标志。
    
    属性:
        idx_org: 端子排号，表示通道在端子排上的原始位置
        type: 通道类型，可以是模拟通道类型或数字通道类型
        flag: 通道标志，用于标识通道的具体用途
    """
    idx_org: int = Field(ge=0, description="端子排号")
    type: AnalogChannelType | DigitalChannelType | None = Field(default=None, description="通道类型")
    flag: AnalogChannelFlag | DigitalChannelFlag | None = Field(default=None, description="通道标识")

    def __str__(self) -> str:
        """
        返回通道的字符串表示形式
        
        返回:
            格式化的字符串，包含通道的主要属性
        """
        attrs = [f"idx_org={self.idx_org}"]
        if self.type:
            attrs.append(f"type={self.type.value}")
        if self.flag:
            attrs.append(f"flag={self.flag.value}")
        return f"DmfChannel({', '.join(attrs)})"
