#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import ConfigDict, Field

from comtrade_io.base import ReferenceBaseModel
from comtrade_io.channel.channel import ChannelBaseModel
from comtrade_io.type import Contact


class Status(ChannelBaseModel, ReferenceBaseModel):
    """数字量通道类

    表示COMTRADE配置文件中的数字量（状态量）通道信息。

    属性:
        index: 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        name: 通道标识（ch_id）
        phase: 通道相别标识（ph）
        equip: 被监视的电路元件（ccbm）
        reference: IEC61850参引
        contact: 状态通道正常状态，默认为常开
        data: 通道数据，一维数组
    """
    model_config = ConfigDict(extra="allow")
    contact: Contact = Field(default=Contact.NormallyOpen, description="状态通道正常状态")
    equipment_no: Optional[str] = Field(
        default=None, description="保护/断路器/刀闸序号，如Relay_#1、Breaker_#1"
    )

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将数字量通道对象转换为COMTRADE配置文件格式的字符串。

        返回:
            str: 逗号分隔的通道信息字符串
        """
        return super().__str__() + f",{self.contact.value}"

    def to_dmf(self):
        """将数字量通道对象转换为DMF格式字符串

        返回:
            str: DMF格式的XML字符串
        """
        attrs = [
            f'idx_cfg="{self.index}"',
            f'idx_org="{self.idx_org}"',
            f'type="{self.type.value if self.type else ""}"',
            f'flag="{self.flag.value if self.flag else ""}"',
            f'contact="{self.contact.name}"',
            f'srcRef="{self.reference}"'
        ]
        return f"\t<scl:StatusChannel {' '.join(attrs)} />"

    def to_inf(self):
        """将数字量通道对象转换为INF格式字符串

        返回:
            str: INF格式的字符串
        """
        attrs = [
            f"[Public Status_Channel_#{self.index}]",
            f"Channel_ID={self.name}",
            f"Phase_ID={self.phase.value}",
            f"Monitored_Component={self.reference}",
            f"Normal_State={self.contact.value}"
        ]
        return "\n".join(attrs)
