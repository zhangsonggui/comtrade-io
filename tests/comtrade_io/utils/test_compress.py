#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试文件压缩工具
"""
import tempfile
from pathlib import Path

from comtrade_io.utils.file_compressor import compress_files, FileCompressor


class TestFileCompressor:
    """测试文件压缩类"""

    def setup_method(self):
        """创建临时测试目录"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.output_dir = Path(tempfile.mkdtemp())
        self.create_test_files()

    def teardown_method(self):
        """清理临时目录"""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def create_test_files(self):
        """创建测试文件"""
        # 创建子目录
        subdir = self.test_dir / "subdir"
        subdir.mkdir()

        # 在主目录创建文件
        (self.test_dir / "test1.cfg").write_text("config data")
        (self.test_dir / "test2.dat").write_text("data content")
        (self.test_dir / "test3.hdr").write_text("header info")

        # 在子目录创建文件
        (subdir / "test4.cfg").write_text("subdir config")

    def test_compress_files_basic(self):
        """测试基本压缩功能"""
        files = [
            self.test_dir / "test1.cfg",
            self.test_dir / "test2.dat",
        ]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name="test.zip",
            preserve_structure=True,
        )

        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        assert zip_path.parent == self.output_dir

        # 验证压缩包内容
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            assert "test1.cfg" in namelist
            assert "test2.dat" in namelist
            assert len(namelist) == 2

    def test_compress_files_with_nonexistent_files(self):
        """测试包含不存在文件的压缩"""
        files = [
            self.test_dir / "test1.cfg",
            self.test_dir / "nonexistent.txt",  # 不存在的文件
            self.test_dir / "test2.dat",
        ]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name="test.zip",
            preserve_structure=True,
        )

        # 应该只压缩存在的文件
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            assert "test1.cfg" in namelist
            assert "test2.dat" in namelist
            assert "nonexistent.txt" not in namelist
            assert len(namelist) == 2

    def test_compress_files_preserve_structure(self):
        """测试保留路径结构"""
        files = [
            self.test_dir / "test1.cfg",
            self.test_dir / "subdir" / "test4.cfg",
        ]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name="test.zip",
            preserve_structure=True,
        )

        # 验证保留相对路径
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            assert "test1.cfg" in namelist
            assert (
                "subdir/test4.cfg" in namelist or "subdir\\test4.cfg" in namelist
            )  # Windows 路径分隔符
            assert len(namelist) == 2

    def test_compress_files_no_preserve_structure(self):
        """测试不保留路径结构（扁平化）"""
        files = [
            self.test_dir / "test1.cfg",
            self.test_dir / "subdir" / "test4.cfg",
        ]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name="test.zip",
            preserve_structure=False,
        )

        # 所有文件应该在根目录
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            assert "test1.cfg" in namelist
            assert "test4.cfg" in namelist
            assert len(namelist) == 2

    def test_compress_files_with_string_paths(self):
        """测试使用字符串路径"""
        files = [
            str(self.test_dir / "test1.cfg"),
            str(self.test_dir / "test2.dat"),
        ]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=str(self.output_dir),
            zip_name="test.zip",
            preserve_structure=True,
        )

        assert zip_path.exists()

    def test_compress_files_empty_list(self):
        """测试空文件列表"""
        files = []
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name="empty.zip",
            preserve_structure=True,
        )

        # 应该创建空的 zip 文件
        assert zip_path.exists()
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zipf:
            assert len(zipf.namelist()) == 0

    def test_compress_files_all_nonexistent(self):
        """测试所有文件都不存在的情况"""
        files = [
            self.test_dir / "nonexistent1.txt",
            self.test_dir / "nonexistent2.txt",
        ]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name="empty.zip",
            preserve_structure=True,
        )

        # 应该创建空的 zip 文件
        assert zip_path.exists()
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zipf:
            assert len(zipf.namelist()) == 0

    def test_function_interface(self):
        """测试函数接口"""
        files = [
            self.test_dir / "test1.cfg",
            self.test_dir / "test2.dat",
        ]
        zip_path = compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name="test.zip",
            preserve_structure=True,
        )

        assert zip_path.exists()
        import zipfile

        with zipfile.ZipFile(zip_path, "r") as zipf:
            namelist = zipf.namelist()
            assert len(namelist) == 2

    def test_output_dir_created_if_not_exists(self):
        """测试输出目录不存在时自动创建"""
        new_output_dir = self.output_dir / "new_subdir"
        assert not new_output_dir.exists()

        files = [self.test_dir / "test1.cfg"]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=new_output_dir,
            zip_name="test.zip",
            preserve_structure=True,
        )

        assert new_output_dir.exists()
        assert zip_path.exists()

    def test_zip_name_none_generates_timestamp(self):
        """测试不传入 zip_name 时自动生成时间戳文件名"""
        files = [self.test_dir / "test1.cfg"]
        zip_path = FileCompressor.compress_files(
            files=files,
            output_dir=self.output_dir,
            zip_name=None,  # 不传入 zip_name
            preserve_structure=True,
        )

        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        # 检查文件名是否符合时间戳格式（如 20260224_150223_231.zip）
        name_without_ext = zip_path.stem
        parts = name_without_ext.split("_")
        assert len(parts) == 3  # YYYYMMDD_HHMMSS_mmm
        assert len(parts[0]) == 8  # 日期部分 20260224
        assert len(parts[1]) == 6  # 时间部分 150223
        assert len(parts[2]) == 3  # 毫秒部分 231
