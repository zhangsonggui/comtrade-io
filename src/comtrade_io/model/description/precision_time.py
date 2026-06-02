#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime

from pydantic import BaseModel, Field

# 支持的时间格式列表，按优先级排序
time_formats = (
    "%d/%m/%Y,%H:%M:%S.%f",  # 四位年，欧洲格式（日/月/年）
    "%m/%d/%Y,%H:%M:%S.%f",  # 四位年，美国格式（月/日/年）
    "%m/%d/%y,%H:%M:%S.%f",  # 两位年，美国格式（月/日/年）
    "%d/%m/%y,%H:%M:%S.%f",  # 两位年，美国格式（日/月/年）
    "%d/%m/%Y, %H:%M:%S.%f",  # 四位年，欧洲格式，带空格
    "%Y-%m-%d %H:%M:%S",  # ISO日期格式，无微秒
    "%Y-%m-%d %H:%M:%S.%f",  # ISO日期格式，带微秒
    "%Y-%m-%dT%H:%M:%S.%f",  # ISO日期格式，带微秒
    "%Y-%m-%d,%H:%M:%S.%f",  # ISO日期格式，逗号分隔，带微秒
    "%Y/%m/%d %H:%M:%S",  # 斜杠分隔的年月日格式
    "%Y/%m/%d %H:%M:%S.%f",  # 带微秒的斜杠分隔格式
    "%d/%m/%Y %H:%M:%S",  # 欧洲常用格式，空格分隔
    "%d/%m/%Y %H:%M:%S.%f",  # 带微秒的欧洲常用格式
    "%m/%d/%Y %H:%M:%S",  # 美国常用格式，空格分隔
    "%m/%d/%Y %H:%M:%S.%f",  # 带微秒的美国常用格式
)


def format_time(str_time: str) -> datetime:
    """解析时间字符串为datetime对象

    支持多种常见的时间格式，按优先级尝试解析。

    参数:
        str_time: 时间字符串，也可以直接是datetime对象

    返回:
        datetime: 解析后的datetime对象

    异常:
        ValueError: 当时间字符串格式无法解析时抛出异常
    """
    if isinstance(str_time, datetime):
        return str_time

    str_time = str_time.strip()
    if "." in str_time:
        parts = str_time.split(".")
        base = parts[0]
        microsecond = parts[1].ljust(6, "0")[:6]
        str_time = base + "." + microsecond
    for fmt in time_formats:
        try:
            return datetime.strptime(str_time, fmt)
        except ValueError:
            if "29" in str_time and ("02/" in str_time or "/02/" in str_time):
                try:
                    modified_time = str_time.replace("/29/", "/28/")
                    return datetime.strptime(modified_time, fmt)
                except ValueError:
                    continue
            continue
    raise ValueError(f"时间格式错误: {str_time}")


class PrecisionTime(BaseModel):
    """精度时间类

    表示COMTRADE文件中的高精度时间戳，精确到微秒级别。

    属性:
        time: 精确时间，精确到微秒
    """
    time: datetime = Field(default_factory=datetime.now, description="时间")

    def __str__(self) -> str:
        """序列化为标准时间字符串

        将datetime对象转换为 'yyyy-mm-dd hh:mm:ss.ffffff' 格式的字符串

        返回:
            str: 格式化的时间字符串
        """
        return self.time.strftime("%m/%d/%Y,%H:%M:%S.%f")
