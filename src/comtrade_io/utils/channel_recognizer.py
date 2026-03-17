#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通道识别模块：根据通道名称自动识别通道类型和标志

提供从通道名称自动识别：
- AnalogChannelType (交流/直流/其他)
- AnalogChannelFlag (电压/电流/频率/功率等)
"""

import json
import re
from pathlib import Path
from typing import Optional, Tuple

from comtrade_io.type import AnalogChannelFlag, AnalogChannelType


class ChannelPatternConfig:
    """通道模式配置"""

    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化通道模式配置

        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 使用默认配置文件路径
            config_file = Path(__file__).parent.parent / 'config' / 'channel_patterns.json'

        self.config_file = config_file
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if not self.config_file.exists():
            raise FileNotFoundError(f"通道模式配置文件不存在: {self.config_file}")

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        self.type_patterns = config.get('analog_channel_type_patterns', [])
        self.flag_patterns = config.get('analog_channel_flag_patterns', [])
        self.default_values = config.get('default_values', {
            'type': 'A',
            'flag': 'ACV'
        })

    def reload(self):
        """重新加载配置文件"""
        self._load_config()


class ChannelRecognizer:
    """通道识别器：根据通道名称识别类型和标志"""

    def __init__(self, config: Optional[ChannelPatternConfig] = None):
        """
        初始化通道识别器

        Args:
            config: 通道模式配置，如果为None则使用默认配置
        """
        self.config = config or ChannelPatternConfig()

    def recognize_type(self, channel_name: str) -> AnalogChannelType:
        """
        根据通道名称识别通道类型

        Args:
            channel_name: 通道名称

        Returns:
            AnalogChannelType: 识别的通道类型
        """
        if not channel_name:
            return AnalogChannelType.from_value(self.config.default_values['type'])

        # 按顺序匹配类型模式
        for pattern_config in self.config.type_patterns:
            for pattern_str in pattern_config['patterns']:
                try:
                    if re.fullmatch(pattern_str, channel_name, re.IGNORECASE):
                        return AnalogChannelType.from_value(pattern_config['type'])
                except re.error as e:
                    # 正则表达式错误，跳过
                    continue

        # 默认返回交流类型
        return AnalogChannelType.from_value(self.config.default_values['type'])

    def recognize_flag(self, channel_name: str) -> AnalogChannelFlag:
        """
        根据通道名称识别通道标志

        Args:
            channel_name: 通道名称

        Returns:
            AnalogChannelFlag: 识别的通道标志
        """
        if not channel_name:
            return AnalogChannelFlag.from_value(self.config.default_values['flag'])

        # 存储匹配结果和优先级
        matches = []

        # 匹配标志模式
        for pattern_config in self.config.flag_patterns:
            for pattern_str in pattern_config['patterns']:
                try:
                    if re.fullmatch(pattern_str, channel_name, re.IGNORECASE):
                        priority = pattern_config.get('priority', 0)
                        matches.append((
                            priority,
                            pattern_config['flag']
                        ))
                except re.error as e:
                    # 正则表达式错误，跳过
                    continue

        # 选择优先级最高的匹配
        if matches:
            # 按优先级降序排序
            matches.sort(key=lambda x: x[0], reverse=True)
            return AnalogChannelFlag.from_value(matches[0][1])

        # 默认返回电压标志
        return AnalogChannelFlag.from_value(self.config.default_values['flag'])

    def recognize(self, channel_name: str) -> Tuple[AnalogChannelType, AnalogChannelFlag]:
        """
        根据通道名称识别类型和标志

        Args:
            channel_name: 通道名称

        Returns:
            (AnalogChannelType, AnalogChannelFlag): 识别的类型和标志
        """
        channel_type = self.recognize_type(channel_name)
        channel_flag = self.recognize_flag(channel_name)
        return channel_type, channel_flag

    def reload_patterns(self):
        """重新加载模式配置"""
        self.config.reload()


# 全局单例识别器
_recognizer: Optional[ChannelRecognizer] = None


def get_recognizer() -> ChannelRecognizer:
    """
    获取全局通道识别器单例

    Returns:
        ChannelRecognizer: 通道识别器实例
    """
    global _recognizer
    if _recognizer is None:
        _recognizer = ChannelRecognizer()
    return _recognizer


def recognize_channel_type(channel_name: str) -> AnalogChannelType:
    """
    识别通道类型（便捷函数）

    Args:
        channel_name: 通道名称

    Returns:
        AnalogChannelType: 识别的通道类型
    """
    return get_recognizer().recognize_type(channel_name)


def recognize_channel_flag(channel_name: str) -> AnalogChannelFlag:
    """
    识别通道标志（便捷函数）

    Args:
        channel_name: 通道名称

    Returns:
        AnalogChannelFlag: 识别的通道标志
    """
    return get_recognizer().recognize_flag(channel_name)


def recognize_channel(channel_name: str) -> Tuple[AnalogChannelType, AnalogChannelFlag]:
    """
    识别通道类型和标志（便捷函数）

    Args:
        channel_name: 通道名称

    Returns:
        (AnalogChannelType, AnalogChannelFlag): 识别的类型和标志
    """
    return get_recognizer().recognize(channel_name)


def reload_channel_patterns():
    """重新加载通道模式配置（便捷函数）"""
    get_recognizer().reload_patterns()
