#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from pydantic import BaseModel, Field

from comtrade_io.utils.str_split import str_split


class Segment(BaseModel):
    """采样点率模型

    描述单条采样段信息，包含采样点数和结束点。
    用于定义COMTRADE文件中各采样段的采样率配置。

    字符串表示形如: "1920,1000"

    属性:
        samp: 采样点数，每个采样段的采样点数量，必须大于0
        end_point: 结束采样点数，该采样段结束时的累计采样点数，必须大于0
    """
    samp: int = Field(..., description="采样点数", gt=0)
    end_point: int = Field(..., description="结束采样点数", gt=0)

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将采样点率对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的字符串，格式为 "samp,end_point"
        """
        return f"{self.samp},{self.end_point}"

    @classmethod
    def from_str(cls, _str: str) -> 'Segment|None':
        """从逗号分隔的字符串反序列化采样点率

        将配置文件中的采样段字符串解析为Nrate对象。
        例如: '1920,1000' 表示该段有1920个采样点，结束点为1000。

        参数:
            _str: 逗号分隔的采样点率字符串

        Returns:
            Segment: 解析后的采样点率对象；如果采样点或结束点为0则返回None
        """
        if not isinstance(_str, str):
            return None
        parts = str_split(_str)
        samp = int(float(parts[0]))
        end_point = int(parts[1])
        if samp == 0 or end_point == 0:
            return None
        return cls(samp=samp, end_point=end_point)

    @classmethod
    def from_dict(cls, data: dict) -> 'Segment':
        """从字典反序列化采样点率

        将包含采样点率信息的字典解析为Nrate对象。

        参数:
            data: 包含samp和end_point字段的字典

        Returns:
            Segment: 解析后的采样点率对象

        异常:
            ValueError: 当缺少必填字段时抛出
        """
        if 'samp' not in data or 'end_point' not in data:
            raise ValueError("缺少必填字段")
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'Segment':
        data = json.loads(json_str)
        return cls.from_dict(data)
