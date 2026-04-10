#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from typing import Optional

from pydantic import Field

from comtrade_io.base.channel import ChannelBaseModel
from comtrade_io.type.phase import Phase
from comtrade_io.utils.str_split import str_split


class ChannelCfgBaseModel(ChannelBaseModel):
    """
    Cfg通道基类

    参数:
        index(int): 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        name(str): 通道标识（ch_id）
        phase(Phase): 通道相别标识（ph）
        equip(str): 被监视的电路元件（ccbm）
    返回:
        Channel对象
    """
    equip: Optional[str] = Field(default='', description="被监视的电路元件")

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将通道基类对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的字符串，格式为 "index,name,phase,equip"
        """
        return f"{super().__str__()},{self.equip}"

    @classmethod
    def from_dict(cls, data: dict) -> 'ChannelCfgBaseModel':
        """从字典反序列化"""
        name = data.get("name", None)
        if not name:
            raise ValueError(f"传入的参数错误,缺少必填字段name")
        phase = data.get("phase", "")
        if isinstance(phase, str):
            data['phase'] = Phase.from_value(phase)
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'ChannelCfgBaseModel':
        """从JSON字符串反序列化"""
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def from_str(cls, _str: str) -> 'ChannelCfgBaseModel':
        """从逗号分隔的字符串反序列化通道对象

        将配置文件中的通道信息字符串解析为CfgChannelBaseModel对象。
        字符串格式为: "index,name,phase,equip"

        参数:
            _str: 逗号分隔的通道字符串

        Returns:
            ChannelCfgBaseModel: 解析后的通道对象

        异常:
            ValueError: 当字符串格式不正确或缺少必填字段时抛出
        """
        str_arr = str_split(_str)
        if (arr_len := len(str_arr)) < 2:
            raise ValueError(f"字符串分割后数组为[{str_arr}],长度不足")
        channel = cls(index=int(str_arr[0]), name=str_arr[1])
        if arr_len >= 3:
            channel.phase = Phase.from_value(str_arr[2], Phase.NONE)
        if arr_len >= 4:
            channel.equip = str_arr[3]
        return channel
