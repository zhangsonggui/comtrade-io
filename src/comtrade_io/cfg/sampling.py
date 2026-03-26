#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""采样信息模型
描述：用于描述波形的采样信息，包含频率和采样段列表。
"""
import json
from typing import List, Optional

from comtrade_io.cfg.segment import Segment
from comtrade_io.utils import get_logger
from pydantic import BaseModel, Field

logging = get_logger()


class Sampling(BaseModel):
    freq: Optional[float] = Field(default=50.0, description="电网频率")
    segments: List[Segment] = Field(default_factory=list, description="采样段")

    def __str__(self) -> str:
        """序列化为多行文本

        将采样信息对象转换为COMTRADE配置文件格式的多行字符串。
        第一行为采样频率，后续行为各采样段信息。

        Returns:
            str: 多行字符串，第一行为频率，后续行为NRATE行
        """
        freq_str = f"{self.freq}"
        segments_len = len(self.segments)
        segment_str = '\n'.join([str(segment) for segment in self.segments])
        if segment_str:
            return f"{freq_str}\n{segments_len}\n{segment_str}"
        return freq_str

    @classmethod
    def from_str(cls, _str: str) -> 'Sampling':
        """从多行字符串反序列化采样信息

        将配置文件中的采样信息字符串解析为Sampling对象。
        第一行为采样频率，后续每行为一个Segment采样段。
        支持仅包含频率一行的情况（segment为空）。

        参数:
            _str: 多行字符串，第一行为频率，后续行为NRATE行

        Returns:
            Sampling: 解析后的采样信息对象
        """
        if not _str or _str.strip() == '':
            return cls()
        lines = [ln.strip() for ln in _str.strip().splitlines() if ln.strip() != '']
        if len(lines) == 0:
            return cls()
        freq = float(lines[0]) if lines[0] != '' else 50.0
        segments: List[Segment] = []
        for line in lines[2:]:
            if line:
                segments.append(Segment.from_str(line))
        return cls(freq=freq, segments=segments)

    @classmethod
    def from_dict(cls, data: dict) -> 'Sampling':
        freq = data.get("freq", 50.0)
        segments_data = data.get("segments", [])
        segments: List[Segment] = []
        for item in segments_data:
            if isinstance(item, dict):
                segments.append(Segment.from_dict(item))
            elif isinstance(item, str):
                segments.append(Segment.from_str(item))
            else:
                raise ValueError("非法的 Segment 元素类型")
        return cls(freq=freq, segments=segments)

    @classmethod
    def from_json(cls, json_str: str) -> 'Sampling':
        data = json.loads(json_str)
        return cls.from_dict(data)
