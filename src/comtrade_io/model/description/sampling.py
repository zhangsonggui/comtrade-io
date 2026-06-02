#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""采样信息模型
描述：用于描述波形的采样信息，包含频率和采样段列表。
"""
from typing import List

from pydantic import BaseModel, Field, model_validator

from comtrade_io.model.description.segment import Segment

class Sampling(BaseModel):
    freq: float | None = Field(default=50.0, description="电网频率")
    segments: List[Segment] = Field(default_factory=list, description="采样段")

    @model_validator(mode="after")
    def _fix_segment_end_points(self) -> "Sampling":
        """修正Segment的end_point为累计值

        部分COMTRADE文件的segment第二字段存储的是该段采样点数而非累计结束点。
        当检测到end_point非单调递增时，自动进行转换：
          - 将原始值存入 Segment.count
          - 计算累计 end_point
          - 计算 start_point
        """
        segments = self.segments
        if len(segments) < 2:
            return self

        # 检测是否为非累计值：任一后续段 end_point <= 前一段则判定为段采样点数
        is_count_mode = any(
            segments[i].end_point <= segments[i - 1].end_point
            for i in range(1, len(segments))
        )
        if not is_count_mode:
            return self

        cumulative = 0
        for seg in segments:
            count_val = seg.end_point
            object.__setattr__(seg, "count", count_val)
            object.__setattr__(seg, "start_point", cumulative + 1)
            cumulative += count_val
            object.__setattr__(seg, "end_point", cumulative)
        return self

    def __len__(self):
        return len(self.segments)

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
