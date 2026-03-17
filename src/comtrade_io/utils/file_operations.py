#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件操作工具
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Union


class FileOperations:
    """文件操作工具类"""

    @staticmethod
    def find_files(
        directory: Union[str, Path],
        extensions: Union[str, List[str]] = None,
        recursive: bool = False,
        check_readable: bool = True,
    ) -> List[Path]:
        """
        查找指定目录下的文件

        Args:
            directory: 目录路径
            extensions: 后缀名列表，例如 [".cfg", ".dat"]，支持单个字符串或列表，不包含 "." 也可以
            recursive: 是否遍历子目录，默认不遍历
            check_readable: 是否检查文件可读权限，默认检查

        Returns:
            存在且可读的文件路径列表
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return []
        if not dir_path.is_dir():
            return []

        # 处理扩展名格式
        if extensions is None:
            extensions = []
        elif isinstance(extensions, str):
            extensions = [extensions]
        extensions = [ext if ext.startswith(".") else f".{ext}" for ext in extensions]

        # 选择遍历方法
        paths = dir_path.rglob("*") if recursive else dir_path.glob("*")

        # 过滤文件并检查权限
        result = []
        for path in paths:
            if not path.is_file():
                continue
            if extensions and path.suffix not in extensions:
                continue
            if check_readable and not FileOperations._is_readable(path):
                continue
            result.append(path)

        return result

    @staticmethod
    def find_sibling_files(
        file_path: Union[str, Path],
        extensions: Union[str, List[str]] = None,
        check_readable: bool = True,
    ) -> List[Path]:
        """
        查找同目录下指定后缀名的文件

        Args:
            file_path: 参考文件路径
            extensions: 后缀名列表，例如 [".cfg", ".dat"]，支持单个字符串或列表，不包含 "." 也可以
            check_readable: 是否检查文件可读权限，默认检查

        Returns:
            存在且可读的同目录文件路径列表
        """
        path = Path(file_path)
        if not path.exists():
            return []
        if not path.is_file():
            return []

        # 获取同目录所有文件
        return FileOperations.find_files(
            directory=path.parent,
            extensions=extensions,
            recursive=False,
            check_readable=check_readable,
        )

    @staticmethod
    def _is_readable(path: Path) -> bool:
        """检查文件是否可读"""
        try:
            return os.access(str(path), os.R_OK)
        except Exception:
            return False
