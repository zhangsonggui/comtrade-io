#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from comtrade_io.model.description import TimeInfo
from comtrade_io.utils import text_split, get_logger

logger = get_logger()


class TimeInfoParser:
    """时间信息解析器"""

    @classmethod
    def from_str(cls, _str: str) -> TimeInfo:
        """从逗号分隔的字符串反序列化时间信息

        参数:
            _str: 逗号分隔的时间信息字符串，如 "CST,+08:00"

        Returns:
            TimeInfo: 解析后的时间信息对象
        """
        parts = text_split(_str)
        if len(parts) < 2:
            raise ValueError(f"字符串分割后数组为[{parts}],长度不足")
        logger.debug(f"解析TimeInfo: time_code={parts[0]}, local_code={parts[1]}")
        return TimeInfo(time_code=parts[0], local_code=parts[1])

    @classmethod
    def from_dict(cls, data: dict) -> TimeInfo:
        return TimeInfo(**data)

    @classmethod
    def from_json(cls, json_str: str) -> TimeInfo:
        data = json.loads(json_str)
        return cls.from_dict(data)
