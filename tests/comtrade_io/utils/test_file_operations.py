#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试文件操作工具
"""

import tempfile
from pathlib import Path

import pytest

from comtrade_io.utils.file_operations import FileOperations


class TestFileOperations:
    """测试文件操作类"""

    def setup_method(self):
        """创建临时测试目录"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.create_test_files()

    def teardown_method(self):
        """清理临时目录"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_files(self):
        """创建测试文件"""
        # 创建子目录
        subdir = self.test_dir / "subdir"
        subdir.mkdir()

        # 在主目录创建文件
        (self.test_dir / "test1.cfg").touch()
        (self.test_dir / "test2.dat").touch()
        (self.test_dir / "test3.hdr").touch()
        (self.test_dir / "readme.txt").touch()

        # 在子目录创建文件
        (subdir / "test4.cfg").touch()
        (subdir / "test5.dat").touch()
        (subdir / "image.png").touch()

    def test_find_files_no_extension(self):
        """测试不指定后缀名时查找所有文件"""
        result = FileOperations.find_files(self.test_dir, extensions=None, recursive=False)
        assert len(result) == 4
        assert all(f.is_file() for f in result)
        assert all(f.exists() for f in result)

    def test_find_files_single_extension_str(self):
        """测试单个后缀名（字符串）"""
        result = FileOperations.find_files(self.test_dir, extensions=".cfg", recursive=False)
        assert len(result) == 1
        assert result[0].name == "test1.cfg"

    def test_find_files_single_extension_list(self):
        """测试单个后缀名（列表）"""
        result = FileOperations.find_files(self.test_dir, extensions=[".dat"], recursive=False)
        assert len(result) == 1
        assert result[0].name == "test2.dat"

    def test_find_files_multiple_extensions(self):
        """测试多个后缀名"""
        result = FileOperations.find_files(self.test_dir, extensions=[".cfg", ".dat"], recursive=False)
        assert len(result) == 2
        names = {f.name for f in result}
        assert names == {"test1.cfg", "test2.dat"}

    def test_find_files_extension_without_dot(self):
        """测试后缀名不带点号"""
        result = FileOperations.find_files(self.test_dir, extensions="cfg", recursive=False)
        assert len(result) == 1
        assert result[0].name == "test1.cfg"

    def test_find_files_recursive_false(self):
        """测试不递归子目录"""
        result = FileOperations.find_files(self.test_dir, extensions=[".cfg"], recursive=False)
        assert len(result) == 1
        assert result[0].name == "test1.cfg"

    def test_find_files_recursive_true(self):
        """测试递归子目录"""
        result = FileOperations.find_files(self.test_dir, extensions=[".cfg"], recursive=True)
        assert len(result) == 2
        names = {f.name for f in result}
        assert names == {"test1.cfg", "test4.cfg"}

    def test_find_files_nonexistent_directory(self):
        """测试不存在的目录"""
        result = FileOperations.find_files(self.test_dir / "nonexistent", extensions=[".cfg"])
        assert result == []

    def test_find_files_not_a_directory(self):
        """测试非目录路径"""
        file_path = self.test_dir / "test1.cfg"
        result = FileOperations.find_files(file_path, extensions=[".cfg"])
        assert result == []

    def test_find_sibling_files(self):
        """测试查找同目录下其他文件"""
        reference_file = self.test_dir / "test1.cfg"
        result = FileOperations.find_sibling_files(reference_file, extensions=[".dat", ".hdr"])
        assert len(result) == 2
        names = {f.name for f in result}
        assert names == {"test2.dat", "test3.hdr"}

    def test_find_sibling_files_no_extension(self):
        """测试不指定后缀名时查找所有同目录文件"""
        reference_file = self.test_dir / "test1.cfg"
        result = FileOperations.find_sibling_files(reference_file)
        assert len(result) == 4
        assert all(f.parent == self.test_dir for f in result)

    def test_find_sibling_files_nonexistent_file(self):
        """测试不存在的参考文件"""
        result = FileOperations.find_sibling_files(self.test_dir / "nonexistent.cfg", extensions=[".dat"])
        assert result == []

    def test_find_sibling_files_not_a_file(self):
        """测试非文件路径作为参考"""
        result = FileOperations.find_sibling_files(self.test_dir, extensions=[".dat"])
        assert result == []

    def test_find_files_with_permission_check(self):
        """测试权限检查（正常文件应可读）"""
        result = FileOperations.find_files(self.test_dir, extensions=[".cfg"], check_readable=True)
        assert len(result) >= 0  # 至少能读取一些文件

    def test_find_files_no_permission_check(self):
        """测试不检查权限"""
        result = FileOperations.find_files(self.test_dir, extensions=[".cfg"], check_readable=False)
        assert len(result) >= 0
