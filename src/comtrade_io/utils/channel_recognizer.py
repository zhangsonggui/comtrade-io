#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通道识别模块：根据通道名称自动识别通道类型和标志

提供从通道名称自动识别：
- AnalogChannelType (交流/直流/其他)
- AnalogChannelFlag (电压/电流/频率/功率等)
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from comtrade_io.type import AnalogChannelFlag, AnalogChannelType


@dataclass
class ChannelComponents:
    """通道解析结果"""
    device_id: str
    channel_type: AnalogChannelFlag
    phase: str


class ChannelRecognizer:
    """通道识别器：根据通道名称识别类型和标识"""

    TYPE_PATTERNS = [
        (['电压'], AnalogChannelFlag.ACV),
        (['电流'], AnalogChannelFlag.ACC),
        (['高频'], AnalogChannelFlag.HF),
        (['频率', '频率曲线'], AnalogChannelFlag.FQ),
        (['功率'], AnalogChannelFlag.PW),
        (['阻抗'], AnalogChannelFlag.ZX),
        (['直1+', '直1-', '直2+', '直2-', '直+', '直-'], AnalogChannelFlag.CONST),
    ]

    DC_CONST_KEYWORDS = ['直1+', '直1-', '直2+', '直2-', '直+', '直-']
    DC_FREQ_KEYWORDS = ['高频', '频率', '频率曲线']

    PHASE_VOLTAGE = ['Ua', 'Ub', 'Uc', '3U0', '3Uo', 'U1', 'U2']
    PHASE_CURRENT = ['Ia', 'Ib', 'Ic', '3I0', '3Io', 'I1', 'I2', '1Ia', '1Ib', '1Ic', '1a', '1b', '1c', '31o']
    ALL_PHASES = PHASE_VOLTAGE + PHASE_CURRENT

    def recognize_type(self, channel_name: str) -> AnalogChannelType:
        """根据通道名称识别通道类型"""
        if not channel_name:
            return AnalogChannelType.A

        for keyword in self.DC_FREQ_KEYWORDS:
            if keyword in channel_name:
                return AnalogChannelType.D

        for keyword in self.DC_CONST_KEYWORDS:
            if keyword in channel_name:
                return AnalogChannelType.D

        name_upper = channel_name.upper()
        for phase in self.PHASE_VOLTAGE:
            if name_upper.endswith(phase.upper()):
                return AnalogChannelType.A

        return AnalogChannelType.A

    def recognize_flag(self, channel_name: str) -> AnalogChannelFlag:
        """根据通道名称识别通道标志"""
        if not channel_name:
            return AnalogChannelFlag.ACV

        name = channel_name.strip()
        if name == 'P':
            return AnalogChannelFlag.PW
        if name == 'Q':
            return AnalogChannelFlag.PW
        if name == 'f':
            return AnalogChannelFlag.FQ

        for keywords, flag in self.TYPE_PATTERNS:
            for keyword in keywords:
                if keyword in channel_name:
                    return flag

        name_upper = channel_name.upper()
        for phase in self.PHASE_VOLTAGE:
            if name_upper.endswith(phase.upper()):
                return AnalogChannelFlag.ACV

        for phase in self.PHASE_CURRENT:
            if name_upper.endswith(phase.upper()):
                return AnalogChannelFlag.ACC

        return AnalogChannelFlag.ACV

    def extract_device_id(self, channel_name: str) -> str:
        """从通道名称中提取设备标识"""
        if not channel_name:
            return ''

        if channel_name.startswith('模拟量'):
            return channel_name

        type_keywords = [kw for kws, _ in self.TYPE_PATTERNS for kw in kws]
        type_keywords.sort(key=len, reverse=True)

        keyword_idx = -1
        found_keyword = None
        for keyword in type_keywords:
            idx = channel_name.find(keyword)
            if idx >= 0:
                keyword_idx = idx
                found_keyword = keyword
                break

        if keyword_idx >= 0:
            before_keyword = channel_name[:keyword_idx].strip()
            after_keyword = channel_name[keyword_idx + len(found_keyword):].strip()

            if after_keyword:
                parts_after = after_keyword.split()
                if parts_after and parts_after[0].upper() in ('AD1', 'AD2'):
                    after_keyword = ' '.join(parts_after[1:])

            device_id = before_keyword
            if after_keyword:
                phase = self.extract_phase(after_keyword)
                if phase:
                    device_id = (before_keyword + ' ' + after_keyword.replace(phase, '')).strip()

            if not device_id:
                device_id = before_keyword

            return device_id

        phase = self.extract_phase(channel_name)
        if phase:
            idx = channel_name.rfind(phase)
            if idx > 0:
                device_id = channel_name[:idx].strip()
                if device_id:
                    return device_id

        return channel_name

    def extract_phase(self, channel_name: str) -> str:
        """从通道名称中提取相位标识"""
        if not channel_name:
            return ''

        parts = channel_name.split()
        for part in reversed(parts):
            part_upper = part.upper()
            for phase in self.ALL_PHASES:
                if part_upper == phase.upper():
                    return phase
                if part_upper.endswith(phase.upper()):
                    return phase
        return ''

    def parse(self, channel_name: str) -> ChannelComponents:
        """完整解析通道名称，返回各组件"""
        device_id = self.extract_device_id(channel_name)
        flag = self.recognize_flag(channel_name)
        phase = self.extract_phase(channel_name)

        return ChannelComponents(
            device_id=device_id,
            channel_type=flag,
            phase=phase
        )

    def recognize(self, channel_name: str) -> Tuple[AnalogChannelType, AnalogChannelFlag]:
        """识别通道类型和标志"""
        channel_type = self.recognize_type(channel_name)
        channel_flag = self.recognize_flag(channel_name)
        return channel_type, channel_flag


_recognizer: Optional[ChannelRecognizer] = None


def get_recognizer() -> ChannelRecognizer:
    """获取全局通道识别器单例"""
    global _recognizer
    if _recognizer is None:
        _recognizer = ChannelRecognizer()
    return _recognizer


def recognize_channel_type(channel_name: str) -> AnalogChannelType:
    """识别通道类型"""
    return get_recognizer().recognize_type(channel_name)


def recognize_channel_flag(channel_name: str) -> AnalogChannelFlag:
    """识别通道标志"""
    return get_recognizer().recognize_flag(channel_name)


def recognize_channel(channel_name: str) -> Tuple[AnalogChannelType, AnalogChannelFlag]:
    """识别通道类型和标志"""
    return get_recognizer().recognize(channel_name)


def parse_channel(channel_name: str) -> ChannelComponents:
    """解析通道名称，返回各组件"""
    return get_recognizer().parse(channel_name)
