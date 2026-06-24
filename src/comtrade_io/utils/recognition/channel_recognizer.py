#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from dataclasses import dataclass

from comtrade_io.model.type import (
    AnalogChannelFlag,
    AnalogChannelType,
    DigitalChannelFlag,
    DigitalChannelType,
)
from comtrade_io.model.type.base_enum import BaseEnum
from comtrade_io.utils.recognition.analog_recognizer import AnalogRecognizer
from comtrade_io.utils.recognition.status_recognizer import StatusRecognizer


class RecognitionResult(BaseEnum):
    SUCCESS = ("success", "识别成功")
    FAILED = ("failed", "识别失败")
    PARTIAL = ("partial", "部分识别")
    UNUSED = ("unused", "未使用")


@dataclass
class ChannelRecognitionResult:
    voltage_level: int | None
    monitor: str | None
    protection: str | None
    channel_type: AnalogChannelType | DigitalChannelType
    channel_flag: AnalogChannelFlag | DigitalChannelFlag
    result: RecognitionResult


class ChannelRecognizer:
    def __init__(self) -> None:
        self._analog = AnalogRecognizer()
        self._status = StatusRecognizer()

    def recognize_analog(self, channel_name: str) -> ChannelRecognitionResult:
        if self._analog.is_unused(channel_name):
            return ChannelRecognitionResult(
                voltage_level=None,
                monitor=None,
                protection=None,
                channel_type=AnalogChannelType.O,
                channel_flag=AnalogChannelFlag.NONE,
                result=RecognitionResult.UNUSED,
            )

        voltage_level = _format_voltage_level(
            self._analog.extract_voltage(channel_name)
        )
        monitor = self._analog.extract_monitor(channel_name)
        channel_type, channel_flag = self._analog.classify(channel_name)
        result = _recognition_result(
            voltage_level is not None,
            monitor is not None,
            channel_type != AnalogChannelType.O,
            channel_flag not in (AnalogChannelFlag.CONST, AnalogChannelFlag.NONE),
        )

        return ChannelRecognitionResult(
            voltage_level=voltage_level,
            monitor=monitor,
            protection=None,
            channel_type=channel_type,
            channel_flag=channel_flag,
            result=result,
        )

    def recognize_status(self, channel_name: str) -> ChannelRecognitionResult:
        if self._status.is_unused(channel_name):
            return ChannelRecognitionResult(
                voltage_level=None,
                monitor=None,
                protection=None,
                channel_type=DigitalChannelType.Other,
                channel_flag=DigitalChannelFlag.GENERAL,
                result=RecognitionResult.UNUSED,
            )

        info = self._status.identify(channel_name)
        result = _recognition_result(
            _format_voltage_level(info.voltage_level) is not None,
            info.monitored_component is not None,
            info.protection_model is not None,
            info.channel_type != DigitalChannelType.Other,
            info.channel_flag != DigitalChannelFlag.GENERAL,
        )

        return ChannelRecognitionResult(
            voltage_level=_format_voltage_level(info.voltage_level),
            monitor=info.monitored_component,
            protection=info.protection_model,
            channel_type=info.channel_type,
            channel_flag=info.channel_flag,
            result=result,
        )


_recognizer: ChannelRecognizer | None = None


def get_channel_recognizer() -> ChannelRecognizer:
    global _recognizer
    if _recognizer is None:
        _recognizer = ChannelRecognizer()
    return _recognizer


def recognize_analog_channel(channel_name: str) -> ChannelRecognitionResult:
    return get_channel_recognizer().recognize_analog(channel_name)


def recognize_status_channel(channel_name: str) -> ChannelRecognitionResult:
    return get_channel_recognizer().recognize_status(channel_name)


def _format_voltage_level(voltage_level: str | None) -> int | None:
    if not voltage_level:
        return None
    match = re.search(r"(\d{2,3})\s*kV", voltage_level, re.I)
    if not match:
        return None
    return int(match.group(1)) * 1000


def _recognition_result(*recognized_fields: bool) -> RecognitionResult:
    count = sum(recognized_fields)
    if count >= 3:
        return RecognitionResult.SUCCESS
    if count >= 1:
        return RecognitionResult.PARTIAL
    return RecognitionResult.FAILED
