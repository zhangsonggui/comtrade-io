"""时间信息(Time Information)模型

使用 time_code 与 local_code 表示时间区域信息。
"""

import re

from pydantic import BaseModel, Field, field_validator


class TimeInfo(BaseModel):
    """时间信息模型

    Time Information：描述时区信息，包含time_code和local_code的组合。

    字符串表示形如: "CST,+08:00"

    属性:
        time_code: 时区代码，字母数字，长度1-6
        local_code: 本地时区偏移，字母数字，长度1-6
    """

    time_code: str = Field(
        default="+8", description="time_code, alphanumeric, 1-6 chars"
    )
    local_code: str = Field(
        default="+8", description="local_code, alphanumeric, 1-6 chars"
    )

    @field_validator("time_code", "local_code")
    def _validate_code(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("code must be a string")
        if len(v) < 1 or len(v) > 6:
            raise ValueError("code length must be between 1 and 6")
        if not re.match(r"^[A-Za-z0-9+\-]+$", v):
            raise ValueError("code must be alphanumeric")
        return v

    def __str__(self) -> str:
        return f"{self.time_code},{self.local_code}"
