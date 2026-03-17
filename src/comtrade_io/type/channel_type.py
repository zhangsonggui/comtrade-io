#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.type.base_enum import BaseEnum


class AnalogChannelType(BaseEnum):
    A = ('A', "交流")
    D = ('D', "直流")
    O = ('O', "其他")


class DigitalChannelType(BaseEnum):
    RELAY = ("Relay", "保护动作出口")
    BREAKER = ("Breaker", "断路器位置")
    SWITCH = ("Switch", "开关位置")
    WARNING = ("Warning", "装置告警出口")
    OTHER = ("Other", "其他")
