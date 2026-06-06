#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DatFile测试"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from comtrade_io.parser.cfg.cfg import CfgFile
from comtrade_io.parser.dat import DatFile

DATA_DIR = Path(__file__).parent.parent.parent / "dat"
CFG_FILE = DATA_DIR / "binary_1999.cfg"
DAT_FILE = DATA_DIR / "binary_1999.dat"
CSV_FILE = DATA_DIR / "binary_1999.csv"


@pytest.fixture(scope="module")
def comtrade_cfg():
    """从binary_1999.cfg加载配置"""
    return CfgFile.from_file(CFG_FILE)


@pytest.fixture(scope="module")
def comtrade_data(comtrade_cfg):
    """从binary_1999.cfg加载数据，返回DataFrame"""
    return DatFile.from_file(comtrade_cfg, DAT_FILE)


@pytest.fixture(scope="module")
def expected_df():
    """从CSV文件加载期望数据（跳过标题行）"""
    df = pd.read_csv(CSV_FILE, header=None, encoding="gbk", skiprows=1, low_memory=False)
    return df


class TestDataShape:
    """测试数据形状"""

    def test_dataframe_shape(self, comtrade_data, expected_df):
        """验证DataFrame的行列数"""
        row_num, col_num = comtrade_data.shape
        assert row_num == expected_df.shape[0], f"行数不匹配: {row_num} vs {expected_df.shape[0]}"
        expected_col_num = expected_df.shape[1] - 1
        assert col_num == expected_col_num, f"列数不匹配: {col_num} vs {expected_col_num}"


class TestPointColumn:
    """测试点号列（第0列）"""

    def test_point_values(self, comtrade_data, expected_df):
        """验证点号列的值"""
        actual = comtrade_data.iloc[:, 0].values
        expected = expected_df.iloc[:, 0].values
        assert np.array_equal(actual, expected), "点号列值不匹配"


class TestTimeColumn:
    """测试时间列（第1列）"""

    def test_time_values(self, comtrade_data, expected_df):
        """验证时间列的值"""
        actual = comtrade_data.iloc[:, 1].values
        expected = expected_df.iloc[:, 1].values
        assert np.array_equal(actual, expected), "时间列值不匹配"


class TestAnalogColumns:
    """测试模拟量列（第2列及以后）"""

    def test_analog_all_values(self, comtrade_data, expected_df, comtrade_cfg):
        """验证所有模拟量列的值"""
        analog_count = comtrade_cfg.description.channel_num.analog
        for col_idx in range(analog_count):
            actual = comtrade_data.iloc[:, 2 + col_idx].values
            expected = expected_df.iloc[:, 2 + col_idx].values.astype(float)
            max_diff = np.max(np.abs(actual - expected))
            assert max_diff < 0.01, \
                f"模拟量通道{col_idx + 1}值不匹配, 最大差异: {max_diff}"

    def test_analog_first_row(self, comtrade_data, expected_df):
        """验证第一行模拟量值"""
        actual = comtrade_data.iloc[0, 2:6].values
        expected = expected_df.iloc[0, 2:6].values.astype(float)
        max_diff = np.max(np.abs(actual - expected))
        assert max_diff < 0.01, f"第一行模拟量最大差异: {max_diff}"

    def test_analog_last_row(self, comtrade_data, expected_df):
        """验证最后一行模拟量值"""
        actual = comtrade_data.iloc[-1, 2:6].values
        expected = expected_df.iloc[-1, 2:6].values.astype(float)
        max_diff = np.max(np.abs(actual - expected))
        assert max_diff < 0.01, f"最后一行模拟量最大差异: {max_diff}"


class TestDigitalColumns:
    """测试数字量列"""

    def test_digital_all_values(self, comtrade_data, expected_df, comtrade_cfg):
        """验证所有数字量列的值"""
        analog_count = comtrade_cfg.description.channel_num.analog
        digital_count = comtrade_cfg.description.channel_num.status
        for col_idx in range(digital_count):
            col = 2 + analog_count + col_idx
            actual = comtrade_data.iloc[:, col].values
            expected = expected_df.iloc[:, col].values.astype(int)
            assert np.array_equal(actual, expected), \
                f"数字量通道{col_idx + 1}值不匹配"

    def test_digital_first_row_values(self, comtrade_data, expected_df, comtrade_cfg):
        """验证第一行数字量值"""
        analog_count = comtrade_cfg.description.channel_num.analog
        actual = comtrade_data.iloc[0, 2 + analog_count : 2 + analog_count + 10].values
        expected = expected_df.iloc[0, 2 + analog_count:2 + analog_count + 10].values
        assert np.array_equal(actual, expected), \
            f"第一行数字量不匹配: {actual} vs {expected}"


class TestDataConsistency:
    """测试数据一致性"""

    def test_no_nan_in_data(self, comtrade_data):
        """验证数据中没有NaN值"""
        assert not comtrade_data.isna().any().any(), "数据中存在NaN值"

    def test_first_sample_index(self, comtrade_data):
        """验证第一个采样点的索引为1"""
        assert comtrade_data.iloc[0, 0] == 1, "第一个采样点索引应为1"

    def test_last_sample_index(self, comtrade_data):
        """验证最后一个采样点的索引"""
        last_idx = comtrade_data.iloc[-1, 0]
        expected_count = comtrade_data.shape[0]
        assert last_idx == expected_count, f"最后采样点索引应为{expected_count}, 实际为{last_idx}"

    def test_time_increment(self, comtrade_data):
        """验证时间戳增量一致"""
        time_col = comtrade_data.iloc[:, 1].values
        time_diff = np.diff(time_col)
        expected_increment = time_diff[0] if len(time_diff) > 0 else 0
        assert np.all(time_diff == expected_increment), \
            f"时间戳增量不一致: {np.unique(time_diff)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
