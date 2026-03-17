#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟通道模块

定义模拟通道类，继承自Analog和DmfChannel，用于表示电力系统中的模拟量测量通道。
模拟量通道用于采集电压、电流等连续变化的物理量。
"""
from typing import Any, Optional
from xml.etree.ElementTree import Element

import numpy as np
from pydantic import Field, field_serializer

from comtrade_io.cfg import Analog
from comtrade_io.dmf.dmf_channel import DmfChannel
from comtrade_io.type import (AnalogChannelFlag, AnalogChannelType)
from comtrade_io.utils import parse_float, parse_int
from comtrade_io.utils.channel_recognizer import recognize_channel


class AnalogChannel(Analog, DmfChannel):
    """
    模拟通道类
    
    表示电力系统中的模拟量测量通道，用于采集电压、电流等连续变化的物理量。
    继承自Analog和DmfChannel，包含了通道的标幺值、一次侧/二次侧量程等属性。
    
    属性:
        p_min: 通道一次侧量程的最小值，仅对直流类型有效
        p_max: 通道一次侧量程的最大值，仅对直流类型有效
        s_min: 通道二次侧量程的最小值，仅对直流类型有效
        s_max: 通道二次侧量程的最大值，仅对直流类型有效
        freq: 模拟量频率，通常为50Hz或60Hz
        au: 模拟量标幺系数，用于将实际值转换为标幺值
        bu: 模拟量标幺偏移量
        unit_multiplier: 模拟量增益系数，用于单位换算
        data: 通道数据，一维数组
    """
    p_min: float = Field(default=0.0, description="通道一次侧量程的最小值，仅对直流类型有效")
    p_max: float = Field(default=0.0, description="通道一次侧量程的最大值，仅对直流类型有效")
    s_min: float = Field(default=0.0, description="通道二次侧量程的最小值，仅对直流类型有效")
    s_max: float = Field(default=0.0, description="通道二次侧量程的最大值，仅对直流类型有效")
    freq: float = Field(default=50.0, description="模拟量频率")
    au: float = Field(default=1.0, description="模拟量标幺")
    bu: float = Field(default=0.0, description="模拟量标幺")
    unit_multiplier: str = Field(default="", description="模拟量增益系数")
    data: Optional[Any] = Field(default=None, description="通道数据，一维数组")

    @field_serializer('data')
    def serialize_data(self, data: Any) -> Optional[list]:
        if data is None:
            return None
        if isinstance(data, np.ndarray):
            return data.tolist()
        return data

    def __str__(self):
        """
        返回模拟通道的XML字符串表示形式
        
        返回:
            格式化的XML字符串，表示模拟通道的所有属性
        """
        attrs = [
            f'idx_cfg="{self.index}"',
            f'idx_org="{self.idx_org}"',
            f'type="{self.type}"',
            f'flag="{self.flag}"',
            f'freq="{self.freq}"',
            f'au="{self.au}"',
            f'bu="{self.bu}"',
            f'sIUnit="{self.unit}"',
            f'multiplier="{self.unit_multiplier}"',
            f'primary="{self.primary}"',
            f'secondary="{self.secondary}"',
            f'ps="{self.tran_side}"',
            f'ph="{self.phase}"',
        ]
        return f"\t<scl:AnalogChannel {''.join(attrs)} />"

    @classmethod
    def from_xml(cls, element: Element, analog: Optional[Analog] = None) -> "AnalogChannel":
        """从XML元素创建AnalogChannel实例

        参数:
            element (Element): XML元素
            ns (dict, optional): 命名空间映射
            analog (Analog, optional): 用于对比和更新的Analog实例

        返回:
            AnalogChannel: AnalogChannel实例
        """
        _type = AnalogChannelType.from_value(element.get('type', ''))
        _flag = AnalogChannelFlag.from_value(element.get('flag', ''))
        if _type != _flag.type:
            _type = _flag.type
        channel = cls(
            index=parse_int(element.get('idx_cfg', 1)),
            idx_org=parse_int(element.get('idx_org', 1)),
            type=_type,
            flag=_flag,
            p_min=parse_float(element.get('p_min', 0.0)),
            p_max=parse_float(element.get('p_max', 0.0)),
            s_min=parse_float(element.get('s_min', 0.0)),
            s_max=parse_float(element.get('s_max', 0.0)),
            freq=parse_float(element.get('freq', 50.0)),
            au=parse_float(element.get('au', 1.0)),
            bu=parse_float(element.get('bu', 0.0)),
            unit=element.get('sIUnit', ''),
            unit_multiplier=element.get('multiplier', ""),
            phase=element.get('ph', ''),
            primary=parse_float(element.get('primary', 1.0)),
            secondary=parse_float(element.get('secondary', 1.0)),
            tran_side=element.get('ps', '')
        )

        if analog is not None:
            analog_dict = analog.model_dump()
            for key, value in analog_dict.items():
                if hasattr(channel, key):
                    current_value = getattr(channel, key)
                    if current_value != value:
                        setattr(channel, key, value)

        return channel

    @classmethod
    def from_analog(cls, analog: Analog) -> "AnalogChannel":
        """从Analog实例创建AnalogChannel实例

        该方法会自动根据通道名称识别通道类型和标志:
        - AnalogChannelType: 交流(A)、直流(D)、其他(O)
        - AnalogChannelFlag: 电压(ACV)、电流(ACC)、高频(HF)、频率(FQ)等

        参数:
            analog (Analog): Analog实例

        返回:
            AnalogChannel: AnalogChannel实例
        """
        # 将Analog实例转换为字典
        analog_dict = analog.model_dump()

        # 设置必需的 idx_org 字段，默认与 index 相同
        analog_dict['idx_org'] = analog_dict.get('index', 1)

        # 根据通道名称自动识别通道类型和标志
        if analog.name:
            channel_type, channel_flag = recognize_channel(analog.name)
            analog_dict['type'] = channel_type
            analog_dict['flag'] = channel_flag

        # 设置默认频率（如果未指定）
        if 'freq' not in analog_dict or analog_dict.get('freq', 50.0) == 0.0:
            analog_dict['freq'] = 50.0

        # 设置默认标幺系数
        if 'au' not in analog_dict:
            analog_dict['au'] = 1.0
        if 'bu' not in analog_dict:
            analog_dict['bu'] = 0.0

        # 设置默认倍率
        if 'unit_multiplier' not in analog_dict:
            analog_dict['unit_multiplier'] = ""

        # 使用字典创建AnalogChannel实例
        return cls(**analog_dict)
