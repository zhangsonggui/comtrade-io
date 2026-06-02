#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime

from comtrade_io.model.description import PrecisionTime
from comtrade_io.model.description.precision_time import format_time
from comtrade_io.utils import get_logger

logger = get_logger()


class PrecisionTimeParser:
    """精度时间解析器"""

    @classmethod
    def from_str(cls, _str: str) -> PrecisionTime:
        """从字符串反序列化时间对象

        支持多种常见时间格式的自动识别。

        参数:
            _str: 时间字符串

        Returns:
            PrecisionTime: 解析后的时间对象
        """
        time = format_time(_str)
        logger.debug(f"解析时间: {_str} -> {time}")
        return PrecisionTime(time=time)

    @classmethod
    def from_json(cls, json_str: str) -> PrecisionTime:
        """从JSON字符串反序列化精度时间"""
        data = json.loads(json_str)
        t = data.get("time")
        if t is None:
            raise ValueError("缺少 time 字段")
        time = format_time(t)
        return PrecisionTime(time=time)
