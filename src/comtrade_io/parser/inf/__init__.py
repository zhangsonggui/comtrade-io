#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
INF 解析模块

提供 INF（Information）文件的解析能力，将 INF 文本拆分为结构化节数据，
并支持从节数据构建出 Configure（配置）和 EquipmentGroup（设备组）模型对象。

核心类:
    - InfFile: INF 文件解析器，提供 from_file / from_str 入口
    - SectionData: 拆分后的原始节数据容器

主要函数:
    - split_sections: 文本 → SectionData
    - build_configure: SectionData → Configure
    - build_equipment_group: SectionData → EquipmentGroup
"""

from comtrade_io.parser.inf.configure_builder import build_configure
from comtrade_io.parser.inf.equipment_builder import build_equipment_group
from comtrade_io.parser.inf.inf import InfFile
from comtrade_io.parser.inf.text_splitter import (
    SectionData,
    _kv_pairs,
    parse_section_header,
    split_sections,
)

__all__ = [
    "InfFile",
    "SectionData",
    "build_configure",
    "build_equipment_group",
    "split_sections",
    "parse_section_header",
    "_kv_pairs",
]
