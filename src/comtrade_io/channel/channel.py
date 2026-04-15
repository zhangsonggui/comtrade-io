#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Any, Optional

import numpy as np
from pydantic import Field, field_serializer

from comtrade_io.base.index_base import IdxOrgBaseModel
from comtrade_io.type import AnalogChannelFlag, AnalogChannelType, DigitalChannelFlag, DigitalChannelType, Phase
from comtrade_io.utils import str_split


class ChannelType(IdxOrgBaseModel):
    """DMF通道基类

    定义模拟量和开关量通道的通用属性，包括端子排号、通道类型和通道标志。

    属性:
        index: 索引号
        reference: IEC61850参考
        idx_org: 端子排号，表示通道在端子排上的原始位置
        type: 通道类型，可以是模拟通道类型或数字通道类型
        flag: 通道标志，用于标识通道的具体用途
    """
    type: Optional[AnalogChannelType | DigitalChannelType] = Field(default=None, description="通道类型")
    flag: Optional[AnalogChannelFlag | DigitalChannelFlag] = Field(default=None, description="通道标识")


class ChannelBaseModel(ChannelType):
    """通道基类

    定义所有通道的通用属性和方法，是模拟量通道和数字量通道的基础类。

    属性:
        index: 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        reference: IEC61850参考
        idx_org: 端子排号，表示通道在端子排上的原始位置
        type: 通道类型，可以是模拟通道类型或数字通道类型
        flag: 通道标志，用于标识通道的具体用途
        name: 通道标识（ch_id）
        phase: 通道相别标识（ph）
        equip: 被监视的电路元件
        data: 通道数据，一维数组
    """
    name: Optional[str] = Field(default=None, description="通道标识")
    phase: Optional[Phase] = Field(default=Phase.NONE, description="通道相别标识")
    equip: Optional[str] = Field(default=None, description="被监视的电路元件")
    data: Optional[Any] = Field(default=None, description="通道数据，一维数组")

    @field_serializer('data')
    def serialize_data(self, data: Any) -> Optional[list]:
        """序列化通道数据

        将numpy数组转换为列表以便序列化。

        参数:
            data: 通道数据，可以是None、numpy数组或其他类型

        返回:
            Optional[list]: 序列化后的数据列表，或None
        """
        if data is None:
            return None
        if isinstance(data, np.ndarray):
            return data.tolist()
        return data

    def __str__(self) -> str:
        """序列化为逗号分隔的通道字符串

        将通道对象转换为COMTRADE配置文件格式的字符串。

        返回:
            str: 逗号分隔的通道信息字符串
        """
        phase_value = self.phase.value if self.phase else ""
        return f"{self.index},{self.name},{phase_value},{self.equip}"

    @classmethod
    def from_str(cls, _str: str) -> 'ChannelBaseModel':
        """从逗号分隔的字符串反序列化通道对象

        将配置文件中的通道信息字符串解析为ChannelBaseModel对象。
        字符串格式为: "index,name,phase,equip"

        参数:
            _str: 逗号分隔的通道字符串

        返回:
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

    def sync_from(self, other) -> bool:
        """从另一个通道对象同步属性

        同步规则：
        - 如果 self 的属性为 None，用 other 的值更新（不管 other 的值是否为 None）
        - 如果 other 的属性为 None，不进行更新
        - 其他情况，如果值不同则更新

        参数:
            other: 要同步的源通道对象（通常是 Configure 中的通道）
        """
        if self.index != other.index:
            return False
        # 从类而不是实例访问 model_fields 以避免 Pydantic 警告
        for field_name in other.__class__.model_fields:
            self_value = getattr(self, field_name)
            other_value = getattr(other, field_name)

            # 如果 other 的值为 None，不更新
            if other_value is None:
                continue

            # 如果 self 的值为 None，直接用 other 的值更新
            if self_value is None:
                setattr(self, field_name, other_value)
                continue

            # 其他情况，如果值不同则更新
            if self_value != other_value:
                setattr(self, field_name, other_value)
        return True
