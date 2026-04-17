#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.channel.channel import ChannelBaseModel
from comtrade_io.channel.status import Status
from comtrade_io.type import Contact
from comtrade_io.utils import get_logger, text_split

logging = get_logger()


class StatusDispose:
    """
    状态数据处理类
    """

    @staticmethod
    def from_string(_str: str):
        """
        从字符串中解析状态数据
        """
        str_arr = text_split(_str)
        # 使用前4个元素创建基础通道对象 (index, name, phase, equip)
        channel = ChannelBaseModel.from_str(','.join(str_arr[:4]))
        digital_dict = channel.model_dump()
        # 如果有第5个元素,用于contact;否则使用默认值
        if len(str_arr) >= 5:
            digital_dict['contact'] = Contact.from_value(
                    str_arr[4], Contact.NormallyOpen)

        return Status(**digital_dict)
