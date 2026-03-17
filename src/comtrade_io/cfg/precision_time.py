#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from datetime import datetime

from pydantic import BaseModel, Field

time_formats = [
    "%d/%m/%Y,%H:%M:%S.%f",  # 四位年，欧洲格式（日/月/年）
    "%m/%d/%Y,%H:%M:%S.%f",  # 四位年，美国格式（月/日/年）
    "%m/%d/%y,%H:%M:%S.%f",  # 两位年，美国格式（月/日/年）
    "%d/%m/%y,%H:%M:%S.%f",  # 两位年，美国格式（日/月/年）
    "%d/%m/%Y, %H:%M:%S.%f",  # 四位年，欧洲格式，带空格（你提供的例子）
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
]


def format_time(str_time: str) -> datetime:
    """解析时间字符串为datetime对象

    支持多种常见的时间格式：
    - 欧洲格式：dd/mm/yyyy,hh:mm:ss.ffffff
    - 美国格式：mm/dd/yyyy,hh:mm:ss.ffffff
    - ISO格式：yyyy-mm-dd hh:mm:ss.ffffff
    - 斜杠分隔：yyyy/mm/dd hh:mm:ss.ffffff

    参数:
        str_time: 时间字符串

    返回:
        datetime: 解析后的datetime对象

    异常:
        ValueError: 当时间字符串格式无法解析时抛出
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
            # 处理闰年日期错误的情况
            if "29" in str_time and ("02/" in str_time or "/02/" in str_time):
                # 尝试将2月29日替换为2月28日
                try:
                    modified_time = str_time.replace("/29/", "/28/")
                    return datetime.strptime(modified_time, fmt)
                except ValueError:
                    continue
            continue
    raise ValueError(f"时间格式错误")


class PrecisionTime(BaseModel):
    """精度时间类

    表示COMTRADE文件中的高精度时间戳，精确到微秒级别。
    用于记录故障文件开始时间和故障发生时间。

    属性:
        time: 精确时间，精确到微秒
    """
    time: datetime = Field(default=datetime.now(), description="时间")

    def __str__(self) -> str:
        """序列化为标准时间字符串

        将datetime对象转换为 'yyyy-mm-dd hh:mm:ss.ffffff' 格式的字符串

        Returns:
            str: 格式化的时间字符串
        """
        return self.time.strftime("%Y-%m-%d %H:%M:%S.%f")

    @classmethod
    def from_str(cls, _str: str) -> 'PrecisionTime':
        """从字符串反序列化时间对象

        将各种格式的时间字符串解析为PrecisionTime对象。
        支持多种常见格式的自动识别。

        参数:
            _str: 时间字符串，支持多种格式

        Returns:
            PrecisionTime: 解析后的时间对象

        Raises:
            ValueError: 当时间字符串格式无法识别时抛出
        """
        time = format_time(_str)
        return cls(time=time)

    @classmethod
    def from_json(cls, json_str: str) -> 'PrecisionTime':
        """从JSON字符串反序列化精度时间

        解析JSON格式的时间字符串并创建PrecisionTime对象。
        JSON中应包含"time"字段。

        参数:
            json_str: JSON格式的字符串，必须包含"time"字段

        Returns:
            PrecisionTime: 解析后的时间对象

        异常:
            ValueError: 当JSON中缺少time字段或时间格式不正确时抛出
        """
        data = json.loads(json_str)
        t = data.get("time")
        if t is None:
            raise ValueError("缺少 time 字段")
        time = format_time(t)
        return cls(time=time)
