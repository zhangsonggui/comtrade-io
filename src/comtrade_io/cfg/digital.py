#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import Field

from comtrade_io.cfg.cfg_channel_model import CfgChannelBaseModel
from comtrade_io.type import Contact, Phase
from comtrade_io.utils import str_split


class Digital(CfgChannelBaseModel):
    """
    数字量通道类

    参数：
       index(int): 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
       name(str): 通道标识（ch_id）
       phase(Phase): 通道相别标识（ph）
       equip(str): 被监视的电路元件（ccbm）
       contact(Contact): 状态通道正常状态(y),默认为开放
    """
    contact: Contact = Field(default=Contact.NormallyOpen, description="状态通道正常状态")

    def __str__(self) -> str:
        """序列化为逗号分隔的字符串

        将数字量通道对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的通道信息字符串
        """
        return super().__str__() + f",{self.contact.value}"

    @classmethod
    def from_str(cls, _str: str) -> 'Digital':
        """从逗号分隔的字符串反序列化数字量通道

        将配置文件中的数字量通道字符串解析为Digital对象。
        支持带相别和设备信息的完整格式，以及简化格式。

        参数:
            _str: 逗号分隔的数字量通道字符串

        Returns:
            Digital: 解析后的数字量通道对象

        异常:
            ValueError: 当字符串格式不正确时抛出
        """
        str_arr = str_split(_str)
        # 使用前4个元素创建基础通道对象 (index, name, phase, equip)
        channel = super().from_str(','.join(str_arr[:4]))
        digital_dict = channel.model_dump()
        # 如果有第5个元素,用于contact;否则使用默认值
        if len(str_arr) >= 5:
            digital_dict['contact'] = Contact.from_value(
                str_arr[4], Contact.NormallyOpen)
        return cls(**digital_dict)
