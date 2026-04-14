#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import Field

from comtrade_io.base import ReferenceBaseModel
from comtrade_io.channel.channel import ChannelBaseModel
from comtrade_io.type import Contact


class Status(ChannelBaseModel, ReferenceBaseModel):
    """
    数字量通道类

    参数：
       index(int): 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
       name(str): 通道标识（ch_id）
       phase(Phase): 通道相别标识（ph）
       equip(str): 被监视的电路元件（ccbm）
       contact(Contact): 状态通道正常状态(y),默认为开放
       reference(str): IEC61850参引
    """
    contact: Contact = Field(default=Contact.NormallyOpen, description="状态通道正常状态")

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将数字量通道对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的通道信息字符串
        """
        return super().__str__() + f",{self.contact.value}"

    def to_dmf(self):
        """将数字量通道对象转换为DMF模型对象"""
        attrs = [
            f'idx_cfg="{self.index}"',
            f'idx_org="{self.idx_org}"',
            f'type="{self.type.name}"',
            f'flag="{self.flag.name}"',
            f'contact="{self.contact.name}"',
            f'srcRef="{self.reference}"'
        ]
        return f"\t<scl:StatusChannel {''.join(attrs)} />"

    def to_info(self):
        """将数字量通道对象转换为模拟部件模型对象

        将数字量通道对象转换为模拟部件模型对象。

        Returns:
            StatusSection: 模拟部件模型对象
        """
        attrs = [
            f"[Public Status_Channel_#{self.index}]",
            f"Channel_ID={self.name}",
            f"Phase_ID={self.phase.value}",
            f"Monitored_Component={self.reference}",
            f"Normal_State={self.contact.value}"
        ]
        return "\n".join(attrs)
