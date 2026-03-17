#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.type.base_enum import BaseEnum
from comtrade_io.type.channel_type import AnalogChannelType, DigitalChannelType


class AnalogChannelFlag(BaseEnum):
    ACV = ('ACV', AnalogChannelType.A, "电压")
    ACC = ('ACC', AnalogChannelType.A, "电流")
    HF = ('HF', AnalogChannelType.D, "高频")
    FQ = ('FQ', AnalogChannelType.D, "频率")
    AG = ('AG', AnalogChannelType.O, "相位")
    AMP = ('AMP', AnalogChannelType.O, "幅值")
    PW = ('PW', AnalogChannelType.O, "功率")
    ZX = ('ZX', AnalogChannelType.O, "阻抗")
    CONST = ('CONST', AnalogChannelType.O, "常量")
    NONE = ('', AnalogChannelType.O, "常量")


class DigitalChannelFlag(BaseEnum):
    GENERAL = ("general", DigitalChannelType.OTHER, "一般开关量")
    TR = ("Tr", DigitalChannelType.RELAY, "保护跳闸")
    TR_PHS_A = ("TrPhsA", DigitalChannelType.RELAY, "跳A")
    TR_PHS_B = ("TrPhsB", DigitalChannelType.RELAY, "跳B")
    TR_PHS_C = ("TrPhsC", DigitalChannelType.RELAY, "跳C")
    OP_TP = ("OPTP", DigitalChannelType.RELAY, "三跳信号")
    REC_OP_CLS = ("RecOpCls", DigitalChannelType.RELAY, "重合闸")
    BLK_REC = ("BlkRec", DigitalChannelType.RELAY, "永跳信号")
    PROT_TX = ("ProtTx", DigitalChannelType.RELAY, "发信")
    PROT_RV = ("ProtRv", DigitalChannelType.RELAY, "收信")
    HWJ = ("HWJ", DigitalChannelType.BREAKER, "不分相断路器合位")
    TWJ = ("TWJ", DigitalChannelType.BREAKER, "不分相断路器跳位")
    HWJ_PHS_A = ("HWJPhsA", DigitalChannelType.BREAKER, "断路器A相合位")
    HWJ_PHS_B = ("HWJPhsB", DigitalChannelType.BREAKER, "断路器B相合位")
    HWJ_PHS_C = ("HWJPhsC", DigitalChannelType.BREAKER, "断路器C相合位")
    TWJ_PHS_A = ("TWJPhsA", DigitalChannelType.BREAKER, "断路器A相跳位")
    TWJ_PHS_B = ("TWJPhsB", DigitalChannelType.BREAKER, "断路器B相跳位")
    TWJ_PHS_C = ("TWJPhsC", DigitalChannelType.BREAKER, "断路器C相跳位")
    HWJ_HIGHT = ("HWJHight", DigitalChannelType.BREAKER, "变压器高压侧断路器合位")
    HWJ_MEDIUM = ("HWJMedium", DigitalChannelType.BREAKER, "变压器中压侧断路器合位")
    HWJ_LOW = ("HWJLow", DigitalChannelType.BREAKER, "变压器低压侧断路器合位")
    TWJ_HIGHT = ("TWJHight", DigitalChannelType.BREAKER, "变压器高压侧断路器跳位")
    TWJ_MEDIUM = ("TWJMedium", DigitalChannelType.BREAKER, "变压器中压侧断路器跳位")
    TWJ_LOW = ("TWJLow", DigitalChannelType.BREAKER, "变压器低压侧断路器跳位")
    WARN_VT = ("WarnVt", DigitalChannelType.WARNING, "TV断线")
    WARN_CT = ("WarnCt", DigitalChannelType.WARNING, "CT断线")
    WARN_COMM = ("WarnComm", DigitalChannelType.WARNING, "通道告警")
    WARN_GENERAL = ("WarnGeneral", DigitalChannelType.WARNING, "其他告警")
    NONE = ('', DigitalChannelType.OTHER, "常量")
