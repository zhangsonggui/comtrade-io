import tempfile
from pathlib import Path

import pytest

from comtrade_io.comtrade_file import ComtradeFile, FilePath


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

    @pytest.mark.skipif(__import__('sys').platform == 'win32', reason="Windows does not support file permission changes")
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
            fp = FilePath(path=test_file, is_exists=True, is_empty=False, is_readable=True)
            assert fp.is_enabled() is True


class TestComtradeFileFromPath:
    """测试 ComtradeFile.from_path 类方法"""

    def test_from_path_with_none(self):
        """测试 None 值"""
        result = ComtradeFile.from_path(None)
        assert result.cfg_path.path is None
        assert result.dat_path.path is None

    def test_from_path_with_empty_string(self):
        """测试空字符串"""
        result = ComtradeFile.from_path("")
        assert result.cfg_path.path is None

    def test_from_path_with_whitespace_only(self):
        """测试仅空白字符"""
        result = ComtradeFile.from_path("   ")
        assert result.cfg_path.path is None

    def test_from_path_with_cfg_suffix(self):
        """测试 cfg 后缀"""
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "test.cfg"
            cfg_path.write_text("content")
            
            result = ComtradeFile.from_path(cfg_path)
            
            assert result.cfg_path.path == cfg_path
            assert result.cfg_path.is_exists is True
            assert result.cfg_path.is_empty is False

    def test_from_path_with_DAT_suffix(self):
        """测试 DAT 后缀"""
        with tempfile.TemporaryDirectory() as tmp:
            dat_path = Path(tmp) / "test.DAT"
            dat_path.write_text("content")
            
            result = ComtradeFile.from_path(dat_path)
            
            assert result.dat_path.path == dat_path
            assert result.dat_path.is_exists is True

    def test_from_path_with_dmf_suffix(self):
        """测试 dmf 后缀"""
        with tempfile.TemporaryDirectory() as tmp:
            dmf_path = Path(tmp) / "test.dmf"
            dmf_path.write_text("content")
            
            result = ComtradeFile.from_path(dmf_path)
            
            assert result.dmf_path.path == dmf_path
            assert result.dmf_path.is_exists is True

    def test_from_path_with_HDR_suffix(self):
        """测试 HDR 后缀"""
        with tempfile.TemporaryDirectory() as tmp:
            hdr_path = Path(tmp) / "test.HDR"
            hdr_path.write_text("content")
            
            result = ComtradeFile.from_path(hdr_path)
            
            assert result.hdr_path.path == hdr_path
            assert result.hdr_path.is_exists is True

    def test_from_path_with_INF_suffix(self):
        """测试 INF 后缀"""
        with tempfile.TemporaryDirectory() as tmp:
            inf_path = Path(tmp) / "test.INF"
            inf_path.write_text("content")
            
            result = ComtradeFile.from_path(inf_path)
            
            assert result.inf_path.path == inf_path
            assert result.inf_path.is_exists is True

    def test_from_path_preserve_uppercase_suffix(self):
        """测试大写后缀保持大写"""
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "test.CFG"
            cfg_path.write_text("content")
            
            result = ComtradeFile.from_path(cfg_path)
            
            assert result.cfg_path.path == cfg_path
            assert result.dat_path.path.name.endswith(".DAT")
            assert result.hdr_path.path.name.endswith(".HDR")
            assert result.inf_path.path.name.endswith(".INF")

    def test_from_path_preserve_lowercase_suffix(self):
        """测试小写后缀保持小写"""
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "test.cfg"
            cfg_path.write_text("content")
            
            result = ComtradeFile.from_path(cfg_path)
            
            assert result.cfg_path.path == cfg_path
            assert ".dat" in str(result.dat_path.path)
            assert result.dat_path.path.name.endswith(".dat")

    def test_from_path_with_all_files_exist(self):
        """测试所有相关文件都存在"""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / "test"
            base.with_suffix(".cfg").write_text("cfg")
            base.with_suffix(".dat").write_text("dat")
            base.with_suffix(".dmf").write_text("dmf")
            base.with_suffix(".hdr").write_text("hdr")
            base.with_suffix(".inf").write_text("inf")
            
            result = ComtradeFile.from_path(base.with_suffix(".cfg"))
            
            assert result.cfg_path.is_exists is True
            assert result.dat_path.is_exists is True
            assert result.dmf_path.is_exists is True
            assert result.hdr_path.is_exists is True
            assert result.inf_path.is_exists is True

    def test_from_path_with_nonexistent_related_files(self):
        """测试相关文件不存在"""
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "test.cfg"
            cfg_path.write_text("content")
            
            result = ComtradeFile.from_path(cfg_path)
            
            assert result.cfg_path.is_exists is True
            assert result.dat_path.is_exists is False
            assert result.dmf_path.is_exists is False
            assert result.hdr_path.is_exists is False
            assert result.inf_path.is_exists is False

    def test_from_path_with_empty_file(self):
        """测试空文件"""
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "test.cfg"
            cfg_path.write_text("")
            
            result = ComtradeFile.from_path(cfg_path)
            
            assert result.cfg_path.is_exists is True
            assert result.cfg_path.is_empty is True

    def test_from_path_string_input(self):
        """测试字符串输入"""
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "test.cfg"
            cfg_path.write_text("content")
            
            result = ComtradeFile.from_path(str(cfg_path))
            
            assert result.cfg_path.path == cfg_path


class TestComtradeFileRepr:
    """测试 __repr__ 方法"""

    def test_repr_with_files(self):
        """测试有文件时的 repr"""
        with tempfile.TemporaryDirectory() as tmp:
            cfg_path = Path(tmp) / "test.cfg"
            cfg_path.write_text("content")
            
            result = ComtradeFile.from_path(cfg_path)
            repr_str = repr(result)
            
            assert "ComtradeFile" in repr_str
            assert "cfg_path" in repr_str

    def test_repr_with_empty(self):
        """测试空时的 repr"""
        result = ComtradeFile()
        repr_str = repr(result)
        
        assert "ComtradeFile" in repr_str
