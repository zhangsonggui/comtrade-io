#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""时间信息(Time Information)模型
描述：使用 time_code 与 local_code 表示时间区域信息，time_code 为字母数字，local_code 表示相对于 UTC 的时区偏移，长度为 1-6。"""
import re

from pydantic import BaseModel, Field, field_validator


class TimeInfo(BaseModel):
    """时间信息模型

    Time Information：描述时区信息，包含time_code和local_code的组合。
    time_code为字母数字代码，表示时区标识；local_code表示相对于UTC的时区偏移。

    字符串表示形如: "CST,+08:00"

    属性:
        time_code: 时区代码，字母数字，长度1-6
        local_code: 本地时区偏移，字母数字，长度1-6
    """
    time_code: str = Field(..., description="time_code, alphanumeric, 1-6 chars")
    local_code: str = Field(..., description="local_code, alphanumeric, 1-6 chars")

    @field_validator('time_code', 'local_code')
    def _validate_code(cls, v: str) -> str:
        """验证时间代码格式

        确保时间代码是字母数字字符串，长度在1-6之间。

        参数:
            v: 要验证的代码字符串

        Returns:
            str: 验证通过后的代码字符串

        异常:
            ValueError: 当代码不是字符串、长度不在1-6范围内或包含非法字符时抛出
        """
        if not isinstance(v, str):
            raise ValueError("code must be a string")
        if len(v) < 1 or len(v) > 6:
            raise ValueError("code length must be between 1 and 6")
        if not re.match(r'^[A-Za-z0-9+\-]+$', v):
            raise ValueError("code must be alphanumeric")
        return v

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将时间信息对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的时间信息字符串，格式为 "time_code,local_code"
        """
        return f"{self.time_code},{self.local_code}"

    @classmethod
    def from_str(cls, _str: str) -> 'TimeInfo':
        """从逗号分隔的字符串反序列化时间信息

        将配置文件中的时间信息字符串解析为TimeInfo对象。

        参数:
            _str: 逗号分隔的时间信息字符串

        Returns:
            TimeInfo: 解析后的时间信息对象

        异常:
            ValueError: 当字符串格式不正确或字段长度不符合要求时抛出
        """
        from comtrade_io.utils import text_split
        parts = text_split(_str)
        if len(parts) < 2:
            raise ValueError(f"字符串分割后数组为[{parts}],长度不足")
        return cls(time_code=parts[0], local_code=parts[1])

    @classmethod
    def from_dict(cls, data: dict) -> 'TimeInfo':
        """从字典反序列化时间信息

        将包含时间信息字段的字典解析为TimeInfo对象。

        参数:
            data: 包含time_code和local_code字段的字典

        Returns:
            TimeInfo: 解析后的时间信息对象
        """
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'TimeInfo':
        """从JSON字符串反序列化时间信息

        将JSON格式的时间信息字符串解析为TimeInfo对象。

        参数:
            json_str: JSON格式的字符串

        Returns:
            TimeInfo: 解析后的时间信息对象
        """
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
