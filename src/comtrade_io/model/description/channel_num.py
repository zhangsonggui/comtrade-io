#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field


class ChannelNum(BaseModel):
    """通道数量统计模型

    字符串表示形如: "288,96A,192D"，其中
    - total: 通道总数
    - analog: 模拟量通道数
    - digital: 数字量通道数
    """
    total: int = Field(..., description="通道总数", ge=0)
    analog: int = Field(..., description="模拟量通道数", ge=0)
    status: int = Field(..., description="数字量通道数", ge=0)

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将通道数量对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的字符串，格式为 "total,analogA,digitalD"
        """
        return f"{self.total},{self.analog}A,{self.status}D"

    def to_inf(self) -> str:
        """
        将描述文件转换为INF格式字符串

        返回:
            INF格式字符串
        """
        attrs = [
            f"Total_Channel_Count={self.total}",
            f"Analog_Channel_Count={self.analog}",
            f"Status_Channel_Count={self.status}",
        ]
        return "\n".join(attrs)
