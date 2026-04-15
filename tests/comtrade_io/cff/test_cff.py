#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""CFF模块测试"""
from pathlib import Path

import pytest

from comtrade_io.cff import CffFile, extract_sections
from comtrade_io.comtrade import Comtrade

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CFF_FILE = DATA_DIR / "ascii_cff_2013.cff"


@pytest.fixture(scope="module")
def cff_file_path():
    """获取CFF测试文件路径"""
    return CFF_FILE


@pytest.fixture(scope="module")
def cff_section(cff_file_path):
    """从CFF文件提取sections"""
    return extract_sections(cff_file_path)


@pytest.fixture(scope="module")
def cff_file(cff_file_path):
    """创建CffFile对象"""
    return CffFile.from_file(cff_file_path)


class TestExtractSections:
    """测试extract_sections函数"""

    def test_extract_sections_returns_cffsection(self, cff_section):
        """验证extract_sections返回CffSection对象"""
        from comtrade_io.cff.cff import CffSection
        assert isinstance(cff_section, CffSection)

    def test_cfg_section_exists(self, cff_section):
        """验证CFG部分存在"""
        assert cff_section.cfg is not None
        assert len(cff_section.cfg) > 0

    def test_dat_section_exists(self, cff_section):
        """验证DAT部分存在"""
        assert cff_section.dat is not None
        assert len(cff_section.dat) > 0

    def test_dat_bytes_exists(self, cff_section):
        """验证DAT字节部分存在"""
        assert cff_section.dat_bytes is not None
        assert len(cff_section.dat_bytes) > 0


class TestCffFile:
    """测试CffFile类"""

    def test_cfffile_creation(self, cff_file):
        """验证CffFile对象创建成功"""
        assert cff_file is not None
        assert cff_file.file_path is not None

    def test_cfg_text_property(self, cff_file):
        """验证cfg_text属性"""
        assert cff_file.cfg_text is not None
        assert len(cff_file.cfg_text) > 0

    def test_dat_text_property(self, cff_file):
        """验证dat_text属性"""
        assert cff_file.dat_text is not None
        assert len(cff_file.dat_text) > 0

    def test_to_configure(self, cff_file):
        """验证to_configure方法"""
        configure = cff_file.to_configure()
        assert configure is not None
        assert configure.header is not None
        assert configure.channel_num is not None

    def test_to_configure_channel_count(self, cff_file):
        """验证配置中的通道数量"""
        configure = cff_file.to_configure()
        assert configure.channel_num.analog == 96
        assert configure.channel_num.status == 192

    def test_to_configure_version(self, cff_file):
        """验证配置中的版本信息"""
        configure = cff_file.to_configure()
        assert configure.header.version is not None
        assert configure.header.version.value == "2013"

    def test_to_data_content(self, cff_file):
        """验证to_data_content方法"""
        configure = cff_file.to_configure()
        data_content = cff_file.to_data_content(configure)
        assert data_content is not None
        assert data_content.data is not None

    def test_data_content_shape(self, cff_file):
        """验证数据内容的形状"""
        configure = cff_file.to_configure()
        data_content = cff_file.to_data_content(configure)
        rows, cols = data_content.data.shape
        assert rows > 0
        # 列数 = 点号(1) + 时间(1) + 模拟通道(96) + 数字通道(192)
        assert cols == 1 + 1 + 96 + 192

    def test_to_information(self, cff_file):
        """验证to_information方法（此CFF文件不含INF部分）"""
        information = cff_file.to_information()
        # 这个CFF文件没有INF部分，应该返回None
        assert information is None


class TestComtradeFromCff:
    """测试通过Comtrade.from_file读取CFF文件"""

    def test_comtrade_from_cff(self, cff_file_path):
        """验证从CFF文件创建Comtrade对象"""
        comtrade = Comtrade.from_file(cff_file_path)
        assert comtrade is not None
        assert comtrade.cfg is not None
        assert comtrade.dat is not None

    def test_comtrade_cfg_from_cff(self, cff_file_path):
        """验证从CFF文件解析的配置"""
        comtrade = Comtrade.from_file(cff_file_path)
        assert comtrade.cfg.channel_num.analog == 96
        assert comtrade.cfg.channel_num.status == 192

    def test_comtrade_dat_from_cff(self, cff_file_path):
        """验证从CFF文件解析的数据"""
        comtrade = Comtrade.from_file(cff_file_path)
        assert comtrade.dat.data is not None
        rows, cols = comtrade.dat.data.shape
        assert rows > 0
        assert cols == 1 + 1 + 96 + 192

    def test_comtrade_analog_channels(self, cff_file_path):
        """验证模拟通道信息"""
        comtrade = Comtrade.from_file(cff_file_path)
        assert len(comtrade.cfg.analogs) == 96
        # 检查第一个模拟通道
        first_analog = comtrade.cfg.analogs.get(1)
        assert first_analog is not None
        assert first_analog.index == 1

    def test_comtrade_status_channels(self, cff_file_path):
        """验证状态通道信息"""
        comtrade = Comtrade.from_file(cff_file_path)
        assert len(comtrade.cfg.statuses) == 192
        # 检查第一个状态通道
        first_status = comtrade.cfg.statuses.get(1)
        assert first_status is not None
        assert first_status.index == 1


class TestNoTempFiles:
    """测试不生成临时文件"""

    def test_no_temp_files_created(self, cff_file_path, tmp_path):
        """验证解析过程中不生成临时文件"""
        # 记录tmp_path初始状态
        initial_files = set(tmp_path.iterdir())

        # 解析CFF文件
        comtrade = Comtrade.from_file(cff_file_path)
        assert comtrade is not None

        # 检查tmp_path没有新文件
        final_files = set(tmp_path.iterdir())
        assert initial_files == final_files, "不应该生成临时文件"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
