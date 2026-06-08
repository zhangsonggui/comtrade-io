#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from typing import List

from comtrade_io.model.description import Sampling, Segment
from comtrade_io.parser.description.segment_parser import SegmentParser
from comtrade_io.utils import get_logger

logger = get_logger()


class SamplingParser:
    """采样信息解析器"""

    @classmethod
    def from_str(cls, _str: str) -> Sampling:
        """从多行字符串反序列化采样信息

        第一行为采样频率，后续每行为一个Segment采样段。
        支持仅包含频率一行的情况（segment为空）。

        参数:
            _str: 多行字符串

        Returns:
            Sampling: 解析后的采样信息对象
        """
        if not _str or _str.strip() == "":
            logger.debug("采样信息为空，返回默认值")
            return Sampling()

        lines = [ln.strip() for ln in _str.strip().splitlines() if ln.strip() != ""]
        if len(lines) == 0:
            return Sampling()

        freq = float(lines[0]) if lines[0] != "" else 50.0
        logger.debug(f"解析采样频率: {freq}")

        segments: List[Segment] = []
        for line in lines[2:]:
            if line:
                segment = SegmentParser.from_str(line)
                if segment:
                    segments.append(segment)

        return Sampling(freq=freq, segments=segments)

    @classmethod
    def from_dict(cls, data: dict) -> Sampling:
        freq = data.get("freq", 50.0)
        segments_data = data.get("segments", [])
        segments: List[Segment] = []
        for item in segments_data:
            if isinstance(item, dict):
                segments.append(SegmentParser.from_dict(item))
            elif isinstance(item, str):
                seg = SegmentParser.from_str(item)
                if seg:
                    segments.append(seg)
            else:
                raise ValueError("非法的 Segment 元素类型")
        return Sampling(freq=freq, segments=segments)

    @classmethod
    def from_json(cls, json_str: str) -> Sampling:
        data = json.loads(json_str)
        return cls.from_dict(data)
