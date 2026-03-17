#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件压缩工具
"""
from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from comtrade_io.utils.logging import get_logger

logger = get_logger(__name__)


def generate_filename_with_timestamp(suffix: str = ".zip", fmt: str = "%Y%m%d_%H%M%S_%f") -> str:
    """
    以当前时间生成文件名

    Args:
        suffix: 文件后缀（如 ".zip"）
        fmt: 时间格式，默认为 "%Y%m%d_%H%M%S_%f"
            例如: "20260224_150223_231000"

    Returns:
        基于当前时间生成的文件名
    """
    timestamp = datetime.now().strftime(fmt)
    # 去掉微秒部分的后三位（保留前三位）
    if "%f" in fmt:
        parts = timestamp.split("_")
        if len(parts) >= 2:
            microseconds_part = parts[-1]
            if len(microseconds_part) > 3:
                parts[-1] = microseconds_part[:3]
                timestamp = "_".join(parts)
    return f"{timestamp}{suffix}"


class FileCompressor:
    """文件压缩工具类"""

    @staticmethod
    def compress_files(
        files: List[Union[str, Path]],
        output_dir: Union[str, Path],
        zip_name: Optional[str] = None,
        preserve_structure: bool = True,
    ) -> Path:
        """
        压缩文件列表到 ZIP 文件

        Args:
            files: 要压缩的文件路径列表（Path 对象或字符串）
            output_dir: 压缩文件输出目录
            zip_name: 压缩文件名（如 "archive.zip"），如果不传入则使用当前时间生成
            preserve_structure: 是否保留原始路径结构，默认保留。
                - True: 保留文件相对于其公共父目录的相对路径
                - False: 所有文件直接放在压缩包根目录（扁平化）

        Returns:
            压缩文件的完整路径

        Note:
            - 路径不存在或不可读的文件将被跳过
            - 会记录跳过文件的警告信息
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 如果未传入 zip_name，使用时间戳生成
        if zip_name is None:
            zip_name = generate_filename_with_timestamp(suffix=".zip", fmt="%Y%m%d_%H%M%S_%f")

        zip_path = output_dir / zip_name

        files_to_compress = []
        for file in files:
            file_path = Path(file)
            if not file_path.exists():
                logger.warning(f"文件不存在，跳过: {file_path}")
                continue
            if not file_path.is_file():
                logger.warning(f"不是文件，跳过: {file_path}")
                continue
            if not FileCompressor._is_readable(file_path):
                logger.warning(f"文件不可读，跳过: {file_path}")
                continue
            files_to_compress.append(file_path)

        if not files_to_compress:
            logger.warning("没有可压缩的文件")
            # 创建空的 zip 文件
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                pass
            return zip_path

        # 计算公共父目录（仅在保留路径结构时需要）
        common_parent = None
        if preserve_structure and len(files_to_compress) > 1:
            try:
                common_parent = Path(
                    str(files_to_compress[0].parent)
                ).resolve()
                for file_path in files_to_compress[1:]:
                    current = Path(str(file_path.parent)).resolve()
                    # 找到公共父目录
                    while not str(current).startswith(str(common_parent)):
                        common_parent = common_parent.parent
            except Exception:
                # 如果无法计算公共父目录，使用第一个文件的目录
                common_parent = files_to_compress[0].parent

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files_to_compress:
                    # 确定压缩包中的路径
                    if preserve_structure:
                        if common_parent:
                            try:
                                arcname = file_path.relative_to(common_parent)
                            except ValueError:
                                # 如果文件不在公共父目录下，只用文件名
                                arcname = file_path.name
                        else:
                            arcname = file_path.name
                    else:
                        # 扁平化结构，只保留文件名
                        arcname = file_path.name

                    zipf.write(file_path, str(arcname))
                    logger.debug(f"已添加到压缩包: {arcname}")

            logger.info(f"压缩完成: {zip_path} (共 {len(files_to_compress)} 个文件)")
            return zip_path

        except Exception as e:
            logger.error(f"压缩文件时出错: {e}")
            raise

    @staticmethod
    def _is_readable(path: Path) -> bool:
        """检查文件是否可读"""
        try:
            return path.exists() and path.is_file() and path.stat().st_size >= 0
        except Exception:
            return False


def compress_files(
    files: List[Union[str, Path]],
    output_dir: Union[str, Path],
    zip_name: Optional[str] = None,
    preserve_structure: bool = True,
) -> Path:
    """
    压缩文件列表到 ZIP 文件（函数接口）

    Args:
        files: 要压缩的文件路径列表
        output_dir: 压缩文件输出目录
        zip_name: 压缩文件名（如 "archive.zip"），如果不传入则使用当前时间生成
        preserve_structure: 是否保留路径结构

    Returns:
        压缩文件的完整路径
    """
    return FileCompressor.compress_files(files, output_dir, zip_name, preserve_structure)
