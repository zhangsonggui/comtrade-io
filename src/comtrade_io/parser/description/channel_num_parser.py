import json

from ...model.description import ChannelNum
from ...utils import text_split


class ChannelNumParser:
    """通道数解析器"""

    @classmethod
    def _parse_count(cls, text: str) -> int:
        """从文本中提取数字计数

        从包含字母的文本中提取数字部分并转换为整数。
        例如："96A" -> 96，"192D" -> 192

        参数:
            text: 包含数字和字母的文本

        Returns:
            int: 提取出的数字

        异常:
            ValueError: 当文本中未找到数字时抛出
        """
        digits = "".join([c for c in text if c.isdigit()])
        if digits == "":
            raise ValueError("未找到数字计数")
        return int(digits)

    @classmethod
    def from_str(cls, _str: str) -> ChannelNum:
        """从逗号分隔的字符串反序列化通道数量

        将配置文件中的通道数量字符串解析为ChannelNum对象。
        字符串格式为: "total,analogA,digitalD"，如 "288,96A,192D"

        参数:
            _str: 逗号分隔的通道数量字符串

        Returns:
            ChannelNum: 解析后的通道数量对象

        异常:
            ValueError: 当总数不等于模拟量与数字量之和时抛出
        """
        parts = text_split(_str)
        total = int(parts[0])
        analog = cls._parse_count(parts[1])
        status = cls._parse_count(parts[2])
        if total != analog + status:
            raise ValueError("总数不等于模拟量与数字量之和")
        return ChannelNum(total=total, analog=analog, status=status)

    @classmethod
    def from_dict(cls, data: dict) -> ChannelNum:
        """从字典反序列化通道数量

        将包含通道数量信息的字典解析为ChannelNum对象。

        参数:
            data: 包含total、analog、digital字段的字典

        Returns:
            ChannelNum: 解析后的通道数量对象

        异常:
            ValueError: 当缺少必填字段时抛出
        """
        total = data.get("total")
        analog = data.get("analog")
        status = data.get("status")
        if total is None or analog is None or status is None:
            raise ValueError("缺少必填字段")
        return ChannelNum(total=total, analog=analog, status=status)

    @classmethod
    def from_json(cls, json_str: str) -> ChannelNum:
        """从JSON字符串反序列化通道数量

        将JSON格式的通道数量字符串解析为ChannelNum对象。

        参数:
            json_str: JSON格式的字符串

        Returns:
            ChannelNum: 解析后的通道数量对象
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
