import json

from ...model.description import Header
from ...model.type import Version
from ...utils import text_split, get_logger

logger = get_logger()


class HeaderParser:

    @classmethod
    def from_str(cls, _str: str) -> Header:
        """从逗号分隔的字符串反序列化文件头

        将包含变电站名称、录波设备和版本号的字符串解析为Header对象。

        参数:
            _str: 逗号分隔的文件头字符串，如 "变电站,录波器,1991"

        返回:
            Header: 解析后的文件头对象
        """
        logger.debug(f"正在解析配置文件第一行内容:{_str}")
        str_arr = text_split(_str, filter_empty=False)
        if len(str_arr) < 2:
            return Header()
        if len(str_arr) < 3:
            return Header(
                station=str_arr[0], recorder=str_arr[1], version=Version.V1991
            )
        return Header(
            station=str_arr[0],
            recorder=str_arr[1],
            version=Version.from_value(str_arr[2], Version.V1991),
        )

    @classmethod
    def from_dict(cls, data: dict) -> Header:
        """从字典反序列化"""
        return Header(**data)

    @classmethod
    def from_json(cls, json_str: str) -> Header:
        """从JSON字符串反序列化"""
        data = json.loads(json_str)
        return cls.from_dict(data)
