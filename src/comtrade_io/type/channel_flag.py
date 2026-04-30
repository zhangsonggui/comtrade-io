#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.type.base_enum import BaseEnum
from comtrade_io.type.channel_type import AnalogChannelType, DigitalChannelType


class AnalogChannelFlag(BaseEnum):
    """模拟量通道标志枚举

    定义模拟量通道的物理量类型，如电压、电流、功率、阻抗等。
    每个枚举值包含：(标志代码, 通道类型, 描述)
    """
    TV = ("ACV", AnalogChannelType.A, "工频交流电压")
    TA = ("ACC", AnalogChannelType.A, "工频交流电流")
    DV = ("DV", AnalogChannelType.D, "直流电压")
    DA = ("DA", AnalogChannelType.D, "直流电流")
    HF = ('HF', AnalogChannelType.D, "高频")
    FQ = ('FQ', AnalogChannelType.D, "频率")
    AG = ('AG', AnalogChannelType.O, "相位")
    AMP = ('AMP', AnalogChannelType.O, "幅值")
    PW = ('PW', AnalogChannelType.O, "功率")
    ZX = ('ZX', AnalogChannelType.O, "阻抗")
    CONST = ('CONST', AnalogChannelType.O, "常量")
    NONE = ('', AnalogChannelType.O, "常量")


class DigitalChannelFlag(BaseEnum):
    """数字量通道标志枚举

    定义数字量通道的信号类型，包括保护跳闸、断路器位置、开关量、告警等。
    每个枚举值包含：(标志代码, 通道类型, 描述)
    """
    GENERAL = ("general", DigitalChannelType.Other, "一般开关量")
    TR = ("Tr", DigitalChannelType.Relay_Act, "保护跳闸")
    Jump_A = ("TrPhsA", DigitalChannelType.Relay_Act, "跳A")
    Jump_B = ("TrPhsB", DigitalChannelType.Relay_Act, "跳B")
    Jump_C = ("TrPhsC", DigitalChannelType.Relay_Act, "跳C")
    Jump_ABC = ("OPTP", DigitalChannelType.Relay_Act, "跳三相")
    Jump_Single_Phase = ("TrSPhs", DigitalChannelType.Relay_Act, "单相跳")
    Close_Break = ("RecOpCls", DigitalChannelType.Relay_Act, "重合闸")
    Jump_For_Keeps = ("BlkRec", DigitalChannelType.Relay_Act, "永跳信号")
    Jump_Between_Phases = ("TrBPhs", DigitalChannelType.Relay_Act, "相间跳")
    Jump_Faster = ("TrFast", DigitalChannelType.Relay_Act, "快速跳")
    Jump_Ground = ("TrGnd", DigitalChannelType.Relay_Act, "接地跳")
    Send = ("ProtTx", DigitalChannelType.Relay_Act, "发信")
    Recv = ("ProtRv", DigitalChannelType.Relay_Act, "收信")
    Jump_Close = ("HWJ", DigitalChannelType.Breaker_Pos, "不分相断路器合位")
    Jump_Break = ("TWJ", DigitalChannelType.Breaker_Pos, "不分相断路器跳位")
    Jump_A_Close = ("HWJPhsA", DigitalChannelType.Breaker_Pos, "断路器A相合位")
    Jump_B_Close = ("HWJPhsB", DigitalChannelType.Breaker_Pos, "断路器B相合位")
    Jump_C_Close = ("HWJPhsC", DigitalChannelType.Breaker_Pos, "断路器C相合位")
    Jump_A_Break = ("TWJPhsA", DigitalChannelType.Breaker_Pos, "断路器A相跳位")
    Jump_B_Break = ("TWJPhsB", DigitalChannelType.Breaker_Pos, "断路器B相跳位")
    Jump_C_Break = ("TWJPhsC", DigitalChannelType.Breaker_Pos, "断路器C相跳位")
    Jump_Close_HIGHT = (
        "HWJHight",
        DigitalChannelType.Breaker_Pos,
        "变压器高压侧断路器合位",
    )
    Jump_Close_MEDIUM = (
        "HWJMedium",
        DigitalChannelType.Breaker_Pos,
        "变压器中压侧断路器合位",
    )
    Jump_Close_LOW = (
        "HWJLow",
        DigitalChannelType.Breaker_Pos,
        "变压器低压侧断路器合位",
    )
    Jump_Break_HIGHT = (
        "TWJHight",
        DigitalChannelType.Breaker_Pos,
        "变压器高压侧断路器跳位",
    )
    Jump_Break_MEDIUM = (
        "TWJMedium",
        DigitalChannelType.Breaker_Pos,
        "变压器中压侧断路器跳位",
    )
    Jump_Break_LOW = (
        "TWJLow",
        DigitalChannelType.Breaker_Pos,
        "变压器低压侧断路器跳位",
    )
    TV_Break = ("WarnVt", DigitalChannelType.Device_Alarm, "TV断线")
    TA_Break = ("WarnCt", DigitalChannelType.Device_Alarm, "CT断线")
    CHNL_FAULT = ("WarnComm", DigitalChannelType.Device_Alarm, "通道告警")
    WARN_GENERAL = ("WarnGeneral", DigitalChannelType.Device_Alarm, "其他告警")
    NONE = ("", DigitalChannelType.Other, "常量")
