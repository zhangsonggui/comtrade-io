#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from comtrade_io.model.description import Segment
from comtrade_io.utils import text_split, get_logger

logger = get_logger()


class SegmentParser:
    """采样点率解析器"""

    @classmethod
    def from_str(cls, _str: str) -> Segment | None:
        """从逗号分隔的字符串反序列化采样点率

        参数:
            _str: 逗号分隔的采样点率字符串，如 "1920,1000"

        Returns:
            Segment: 解析后的采样点率对象；解析失败返回None
        """
        if not isinstance(_str, str):
            logger.warning(f"非法的Segment字符串类型: {type(_str)}")
            return None
        parts = text_split(_str)
        if len(parts) < 2:
            logger.warning(f"Segment字符串格式不足: {_str}")
            return None
        samp = int(float(parts[0]))
        end_point = int(parts[1])
        if samp == 0 or end_point == 0:
            logger.warning(f"Segment采样点或结束点为0，跳过: {_str}")
            return None
        logger.debug(f"解析Segment: samp={samp}, end_point={end_point}")
        return Segment(samp=samp, end_point=end_point)

    @classmethod
    def from_dict(cls, data: dict) -> Segment:
        """从字典反序列化采样点率"""
        if "samp" not in data or "end_point" not in data:
            raise ValueError("缺少必填字段")
        return Segment(**data)

    @classmethod
    def from_json(cls, json_str: str) -> Segment:
        data = json.loads(json_str)
        return cls.from_dict(data)
