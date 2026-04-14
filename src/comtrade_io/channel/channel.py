#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Any, Optional

import numpy as np
from pydantic import Field, field_serializer

from comtrade_io.base.index_base import IdxOrgBaseModel
from comtrade_io.type import AnalogChannelFlag, AnalogChannelType, DigitalChannelFlag, DigitalChannelType, Phase
from comtrade_io.utils import str_split


class ChannelType(IdxOrgBaseModel):
    """
    DMF通道基类

    定义模拟量和开关量通道的通用属性，包括端子排号、通道类型和通道标志。

    属性:
        idx_org: 端子排号，表示通道在端子排上的原始位置
        type: 通道类型，可以是模拟通道类型或数字通道类型
        flag: 通道标志，用于标识通道的具体用途
    """
    type: AnalogChannelType | DigitalChannelType | None = Field(default=None, description="通道类型")
    flag: AnalogChannelFlag | DigitalChannelFlag | None = Field(default=None, description="通道标识")


class ChannelBaseModel(ChannelType):
    """
    通道基类
    参数:
        index(int): 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        idx_org: 端子排号，表示通道在端子排上的原始位置
        type: 通道类型，可以是模拟通道类型或数字通道类型
        flag: 通道标志，用于标识通道的具体用途
        name(str): 通道标识（ch_id）
        phase(Phase): 通道相别标识（ph）
        equip(str): 被监视的电路元件
    返回:
        基础通道对象ChannelBaseModel
    """
    name: Optional[str] = Field(default=None, description="通道标识")
    phase: Optional[Phase] = Field(default=Phase.NONE, description="通道相别标识")
    equip: Optional[str] = Field(default='', description="被监视的电路元件")
    data: Optional[Any] = Field(default=None, description="通道数据，一维数组")

    @field_serializer('data')
    def serialize_data(self, data: Any) -> Optional[list]:
        if data is None:
            return None
        if isinstance(data, np.ndarray):
            return data.tolist()
        return data

    def __str__(self) -> str:
        """序列化为逗号分隔的通道字符串"""
        phase_value = self.phase.value if self.phase else ""
        return f"{self.index},{self.name},{phase_value},{self.equip}"

    @classmethod
    def from_str(cls, _str: str) -> 'ChannelBaseModel':
        """从逗号分隔的字符串反序列化通道对象

        将配置文件中的通道信息字符串解析为CfgChannelBaseModel对象。
        字符串格式为: "index,name,phase,equip"

        参数:
            _str: 逗号分隔的通道字符串

        Returns:
            ChannelBaseModel: 解析后的通道对象

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
