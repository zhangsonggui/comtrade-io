import re
from datetime import datetime

from ...utils import get_logger

logger = get_logger()

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
    """解析时间字符串为datetime对象"""
    if isinstance(str_time, datetime):
        return str_time

    str_time = str_time.strip()
    str_time = re.sub(r"(\d)\s*:\s*(\d)", r"\1:\2", str_time)
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


def format_datetime_for_cfg(dt: datetime) -> str:
    """将 datetime 格式化为 COMTRADE CFG 标准时间字符串"""
    return dt.strftime("%m/%d/%Y,%H:%M:%S.%f")


class DateTimeParser:
    """精度时间解析器"""

    @classmethod
    def from_str(cls, _str: str) -> datetime:
        time = format_time(_str)
        logger.debug(f"解析时间: {_str} -> {time}")
        return time

    @classmethod
    def from_json(cls, json_str: str) -> datetime:
        import json

        data = json.loads(json_str)
        t = data.get("time")
        if t is None:
            raise ValueError("缺少 time 字段")
        return format_time(t)
