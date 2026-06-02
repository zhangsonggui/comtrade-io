#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

from comtrade_io.model.description import SamplingTimeQuality
from comtrade_io.utils import text_split, get_logger

logger = get_logger()


class SamplingTimeQualityParser:
    """采样时间品质解析器"""

    @classmethod
    def from_str(cls, _str: str) -> SamplingTimeQuality:
        """从逗号分隔的字符串反序列化采样时间品质

        参数:
            _str: 逗号分隔的字符串，如 "F,1"

        Returns:
            SamplingTimeQuality: 解析后的采样时间品质对象
        """
        parts = text_split(_str)
        if len(parts) < 2:
            raise ValueError(f"字符串分割后数组为[{parts}],长度不足")
        logger.debug(
            f"解析SamplingTimeQuality: tmq_code={parts[0]}, lcapsec={parts[1]}"
        )
        return SamplingTimeQuality(tmq_code=parts[0], lcapsec=int(parts[1]))

    @classmethod
    def from_dict(cls, data: dict) -> SamplingTimeQuality:
        return SamplingTimeQuality(**data)

    @classmethod
    def from_json(cls, json_str: str) -> SamplingTimeQuality:
        data = json.loads(json_str)
        return cls.from_dict(data)
