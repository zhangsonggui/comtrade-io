#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class AnalogChannelType(BaseEnum):
    """模拟量通道类型枚举

    定义模拟量通道的信号类型：交流、直流或其他。
    """
    A = ('A', "交流")
    D = ('D', "直流")
    O = ('O', "其他")


class DigitalChannelType(BaseEnum):
    """数字量通道类型枚举

    定义数字量通道的信号类型，包括保护动作、断路器位置、开关位置、告警等。
    """
    Relay_Act = ("Relay", "保护动作")
    Breaker_Pos = ("Breaker", "断路器位置")
    Switch_Pos = ("Switch", "开关位置")
    Device_Alarm = ("Warning", "装置故障告警")
    Other = ("Other", "其他")
