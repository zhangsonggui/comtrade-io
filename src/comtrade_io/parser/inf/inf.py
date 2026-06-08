#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from comtrade_io.model.configure import Configure
from comtrade_io.model.equipment import EquipmentGroup
from comtrade_io.parser.inf.configure_builder import build_configure
from comtrade_io.parser.inf.equipment_builder import build_equipment_group
from comtrade_io.parser.inf.text_splitter import SectionData, split_sections
from comtrade_io.utils import FilePath, get_logger

logger = get_logger()


def _read_inf_file(path: str | Path) -> str | None:
    path = Path(path)
    if not path.exists():
        logger.warning(f"INF文件不存在: {path}")
        return None
    try:
        return path.read_text(encoding="gbk", errors="replace")
    except UnicodeDecodeError:
        logger.warning(f"配置文件{path}编码不是GBK编码，尝试使用UTF8解析")
        try:
            return path.read_text(encoding="utf-8", errors="replace")
        except UnicodeDecodeError:
            logger.error(f"无法解析INF文件: {path}")
            return None


@dataclass
class InfFile:
    """INF 文件解析器

    负责读取 INF 文件内容，并提供结构化数据提取方法。
    解析后的节数据保存在 sections 属性中，避免重复解析。
    """

    file_name: Path | None = None
    sections: SectionData | None = None

    def __init__(self, file_name: str | Path | None = None):
        """初始化 InfFile 实例

        通过 FilePath 验证文件可用性，只有文件存在且可读时才设置 file_name。

        参数:
            file_name: INF 文件路径（字符串或 Path），为 None 时保持未设置状态
        """
        if file_name is not None:
            fp = FilePath.from_name(file_name)
            if fp.is_enabled():
                self.file_name = fp.path

    def _read_content(self) -> str | None:
        if self.file_name is None:
            return None
        logger.debug(f"正在读取INF文件: {self.file_name}")
        return _read_inf_file(self.file_name)

    def _ensure_sections(self) -> bool:
        if self.sections is not None:
            return True
        content = self._read_content()
        if content is None:
            return False
        logger.debug("开始解析INF节数据")
        self.sections = split_sections(content)
        logger.info("INF文件解析完成")
        return True

    def to_configure(self, config: Configure | None = None) -> Configure | None:
        if not self._ensure_sections():
            return None
        logger.debug("开始构建Configure...")
        return build_configure(self.sections, config)

    def to_equipment_group(self) -> EquipmentGroup | None:
        if not self._ensure_sections():
            return None
        logger.debug("开始构建EquipmentGroup...")
        return build_equipment_group(self.sections)

    @classmethod
    def from_str(cls, content: str) -> InfFile:
        logger.debug("开始解析INF字符串内容")
        sections = split_sections(content)
        instance = cls()
        instance.sections = sections
        logger.info("INF字符串解析完成")
        return instance

    @classmethod
    def from_file(cls, file_name: str | Path) -> InfFile | None:
        instance = cls(file_name)
        if not instance._ensure_sections():
            return None
        return instance
