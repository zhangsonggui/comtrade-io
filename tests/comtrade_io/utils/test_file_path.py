import tempfile
from pathlib import Path

import pytest

from comtrade_io.utils import FilePath


class TestFilePath:
    """测试 FilePath 类"""

    def test_file_path_default_values(self):
        """测试默认属性值"""
        fp = FilePath()
        assert fp.path is None
        assert fp.is_exists is True
        assert fp.is_empty is False
        assert fp.is_readable is True

    def test_file_path_is_enabled_with_none_path(self):
        """测试 path 为 None 时 is_enabled 返回 False"""
        fp = FilePath()
        assert fp.path is None
        assert fp.is_enabled() is False

    def test_file_path_is_enabled_with_empty_file(self):
        """测试空文件时 is_enabled 返回 False"""
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.cfg"
            test_file.write_text("")
            fp = FilePath(path=test_file)
            assert fp.is_enabled() is False

    def test_file_path_is_enabled_with_not_exists(self):
        """测试文件不存在时 is_enabled 返回 False"""
        fp = FilePath(path=Path("notexist.cfg"))
        assert fp.is_enabled() is False

    @pytest.mark.skipif(
        __import__("sys").platform == "win32",
        reason="Windows does not support file permission changes",
    )
    def test_file_path_is_enabled_with_not_readable(self):
        """测试文件不可读时 is_enabled 返回 False"""
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.cfg"
            test_file.write_text("content")
            import os

            os.chmod(test_file, 0o000)
            fp = FilePath(path=test_file)
            assert fp.is_enabled() is False
            os.chmod(test_file, 0o644)

    def test_file_path_is_enabled_all_valid(self):
        """测试所有条件都满足时 is_enabled 返回 True"""
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.cfg"
            test_file.write_text("content")
            fp = FilePath(
                path=test_file, is_exists=True, is_empty=False, is_readable=True
            )
            assert fp.is_enabled() is True

    def test_file_path_str_with_none(self):
        """测试 __str__ 当 path 为 None 时"""
        fp = FilePath()
        assert "None" in str(fp)

    def test_file_path_str_with_valid_file(self):
        """测试 __str__ 当文件有效时"""
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.cfg"
            test_file.write_text("content")
            fp = FilePath(path=test_file)
            assert "可用" in str(fp)

    def test_file_path_post_init_existing_file(self):
        """测试 model_post_init 对存在的文件设置正确状态"""
        with tempfile.TemporaryDirectory() as tmp:
            test_file = Path(tmp) / "test.cfg"
            test_file.write_text("content")
            fp = FilePath(path=test_file)
            assert fp.is_exists is True
            assert fp.is_empty is False
            assert fp.is_readable is True

    def test_file_path_post_init_non_existing_file(self):
        """测试 model_post_init 对不存在的文件设置正确状态"""
        fp = FilePath(path=Path("nonexistent_file.xyz"))
        assert fp.is_exists is False
        assert fp.is_readable is False
        assert fp.is_empty is True
