#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DataContent测试"""
import tempfile
from pathlib import Path

import pytest

from comtrade_io.data.data_content import DataContent
from comtrade_io.cfg import Analog, ChannelNum, Configure, Digital, Header, Sampling
from comtrade_io.type import DataType


class TestDataContent:
    """DataContent测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_config(self):
        """创建示例配置"""
        return Configure(
            header=Header(station="TEST", recorder="TEST"),
            channel_num=ChannelNum(analog=4, digital=8),
            analogs=[
                Analog(index=1, name="IA", multiplier=1.0, offset=0.0),
                Analog(index=2, name="IB", multiplier=1.0, offset=0.0),
                Analog(index=3, name="IC", multiplier=1.0, offset=0.0),
                Analog(index=4, name="V", multiplier=100.0, offset=0.0),
            ],
            digitals=[
                Digital(index=1, name="D1"),
                Digital(index=2, name="D2"),
                Digital(index=3, name="D3"),
                Digital(index=4, name="D4"),
                Digital(index=5, name="D5"),
                Digital(index=6, name="D6"),
                Digital(index=7, name="D7"),
                Digital(index=8, name="D8"),
            ],
            sampling=Sampling(freq=1000),
            data_type=DataType.BINARY,
        )

    def test_ascii_file_reading(self, temp_dir, sample_config):
        """测试ASCII文件读取"""
        # 创建测试ASCII数据文件
        dat_file = temp_dir / "test.dat"
        data = [
            "0,0.0,100,200,300,400,1,0,1,0,1,0,1,0",
            "1,0.001,101,201,301,401,1,0,1,0,1,0,1,0",
            "2,0.002,102,202,302,402,1,0,1,0,1,0,1,0",
        ]
        dat_file.write_text("\n".join(data), encoding="utf-8")

        # 创建DataContent并读取
        content = DataContent(cfg=sample_config, dat_path=dat_file)
        df = content.read()

        assert df is not None
        assert df.shape[0] == 3  # 3行数据
        assert df.shape[1] == 14  # 2列时间 + 4模拟量 + 8数字量

    def test_binary_file_reading(self, temp_dir, sample_config):
        """测试二进制文件读取"""
        # 创建测试二进制数据文件
        dat_file = temp_dir / "test.dat"

        # 构建二进制数据
        samples = []
        for i in range(3):
            index = i
            timestamp = i * 1000  # 微秒
            analogs = [100 + i, 200 + i, 300 + i, 400 + i]
            digital_word = 0b10101010  # 8个数字量

            # 打包为二进制格式
            binary_data = struct.pack(
                "<ii4hH",
                index,
                timestamp,
                *analogs,
                digital_word
            )
            samples.append(binary_data)

        dat_file.write_bytes(b"".join(samples))

        # 创建DataContent并读取
        content = DataContent(cfg=sample_config, dat_path=dat_file)
        df = content.read()

        assert df is not None
        assert df.shape[0] == 3  # 3行数据
        assert df.shape[1] == 14  # 2列时间 + 4模拟量 + 8数字量

    def test_binary32_file_reading(self, temp_dir):
        """测试BINARY32格式文件读取"""
        config = Configure(
            header=Header(station="TEST", recorder="TEST"),
            channel_num=ChannelNum(analog=2, digital=0),
            analogs=[
                Analog(index=1, name="IA", multiplier=1.0, offset=0.0),
                Analog(index=2, name="IB", multiplier=1.0, offset=0.0),
            ],
            sampling=Sampling(freq=1000),
            data_type=DataType.BINARY32,
        )

        dat_file = temp_dir / "test.dat"
        samples = []
        for i in range(5):
            index = i
            timestamp = i * 1000
            analogs = [1000 + i, 2000 + i]
            binary_data = struct.pack(
                "<ii2i",
                index,
                timestamp,
                *analogs
            )
            samples.append(binary_data)
        dat_file.write_bytes(b"".join(samples))

        content = DataContent(cfg=config, dat_path=dat_file)
        df = content.read()

        assert df is not None
        assert df.shape[0] == 5
        assert df.shape[1] == 4  # 2时间列 + 2模拟量

    def test_analog_value_conversion(self, temp_dir, sample_config):
        """测试模拟量值转换"""
        dat_file = temp_dir / "test.dat"
        data = [
            "0,0.0,10,20,30,4,1,0,1,0,1,0,1,0",
            "1,0.001,11,21,31,5,1,0,1,0,1,0,1,0",
        ]
        dat_file.write_text("\n".join(data), encoding="utf-8")

        content = DataContent(cfg=sample_config, dat_path=dat_file)
        df = content.read()

        # 第4个模拟量的multiplier是100，所以应该被转换
        assert df.iloc[0, 5] == 400  # 4 * 100
        assert df.iloc[1, 5] == 500  # 5 * 100

    def test_empty_digital_channels(self, temp_dir):
        """测试无数字量通道的情况"""
        config = Configure(
            header=Header(station="TEST", recorder="TEST"),
            channel_num=ChannelNum(analog=2, digital=0),
            analogs=[
                Analog(index=1, name="IA", multiplier=1.0, offset=0.0),
                Analog(index=2, name="IB", multiplier=1.0, offset=0.0),
            ],
            sampling=Sampling(freq=1000),
            data_type=DataType.ASCII,
        )

        dat_file = temp_dir / "test.dat"
        data = [
            "0,0.0,100,200",
            "1,0.001,101,201",
        ]
        dat_file.write_text("\n".join(data), encoding="utf-8")

        content = DataContent(cfg=config, dat_path=dat_file)
        df = content.read()

        assert df.shape[1] == 4  # 2时间列 + 2模拟量

    def test_invalid_file_path(self, temp_dir, sample_config):
        """测试无效文件路径"""
        invalid_file = temp_dir / "nonexistent.dat"
        content = DataContent(cfg=sample_config, dat_path=invalid_file)

        with pytest.raises(Exception):
            content.read()

    def test_data_validation(self, temp_dir, sample_config):
        """测试数据验证"""
        dat_file = temp_dir / "test.dat"
        # 创建比配置文件期望更多的数据
        data = [
            "0,0.0,100,200,300,400,1,0,1,0,1,0,1,0",
            "1,0.001,101,201,301,401,1,0,1,0,1,0,1,0",
            "2,0.002,102,202,302,402,1,0,1,0,1,0,1,0",
            "3,0.003,103,203,303,403,1,0,1,0,1,0,1,0",
        ]
        dat_file.write_text("\n".join(data), encoding="utf-8")

        # 修改采样信息使其期望更少的数据点
        sample_config.sampling.nrates[0].end_point = 2

        content = DataContent(cfg=sample_config, dat_path=dat_file)
        df = content.read()

        # 应该仍然读取所有数据，但会有警告
        assert df.shape[0] >= 2

    def test_performance_large_file(self, temp_dir, sample_config):
        """测试大文件性能（基准测试）"""
        dat_file = temp_dir / "large_test.dat"

        # 生成10000行测试数据
        data_lines = []
        for i in range(10000):
            line = f"{i},{i * 0.001},{100 + i},{200 + i},{300 + i},{400 + i},1,0,1,0,1,0,1,0"
            data_lines.append(line)

        dat_file.write_text("\n".join(data_lines), encoding="utf-8")

        import time
        start_time = time.time()
        content = DataContent(cfg=sample_config, dat_path=dat_file)
        df = content.read()
        elapsed_time = time.time() - start_time

        assert df is not None
        assert df.shape[0] == 10000
        # 验证读取性能（应该在合理时间内完成）
        assert elapsed_time < 5.0  # 5秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
