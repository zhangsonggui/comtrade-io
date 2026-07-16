"""DatFile.analog_precision 模拟量精度控制单元测试"""

import numpy as np

from comtrade_io.model.channel import Analog
from comtrade_io.model.configure import Configure
from comtrade_io.model.description import ChannelNum, Description, Sampling, Segment
from comtrade_io.model.type import DataType, Phase
from comtrade_io.parser.dat import DatFile


def _make_config() -> Configure:
    """构造最小 ASCII 配置：1 个模拟量通道，2 个采样点

    原始值 1234 经 multiplier=0.001 转换后为 1.234，便于观察精度截断效果。
    """
    config = Configure()
    config.description = Description()
    config.description.data_type = DataType.ASCII
    config.description.channel_num = ChannelNum(total=1, analog=1, status=0)
    config.description.sampling = Sampling(
        freq=50.0, segments=[Segment(samp=1000, end_point=2)]
    )
    config.analogs[1] = Analog(
        index=1,
        name="Ia",
        phase=Phase.PHASE_A,
        multiplier=0.001,
        offset=0.0,
    )
    return config


# 两行 ASCII 数据：index, timestamp, analog_raw
_ASCII_DATA = "1,0,1234\n2,1000,1234\n"


class TestAnalogPrecision:
    """验证不同精度参数对模拟量小数位的控制"""

    def test_precision_2_truncates_to_two_decimals(self):
        cfg = _make_config()
        df = DatFile.from_str(cfg, _ASCII_DATA, analog_precision=2)
        assert df is not None
        # 1.234 -> 1.23
        np.testing.assert_allclose(df.iloc[:, 2].to_numpy(), [1.23, 1.23], rtol=0)

    def test_precision_3_preserves_three_decimals(self):
        cfg = _make_config()
        df = DatFile.from_str(cfg, _ASCII_DATA, analog_precision=3)
        assert df is not None
        np.testing.assert_allclose(df.iloc[:, 2].to_numpy(), [1.234, 1.234], rtol=0)

    def test_precision_6_allows_full_precision(self):
        cfg = _make_config()
        df = DatFile.from_str(cfg, _ASCII_DATA, analog_precision=6)
        assert df is not None
        np.testing.assert_allclose(df.iloc[:, 2].to_numpy(), [1.234, 1.234], rtol=0)

    def test_precision_below_range_skips_adjustment(self):
        """precision=0 超出 [1,6] 范围，应跳过精度调整，保留原始转换值 1.234"""
        cfg = _make_config()
        df = DatFile.from_str(cfg, _ASCII_DATA, analog_precision=0)
        assert df is not None
        np.testing.assert_allclose(df.iloc[:, 2].to_numpy(), [1.234, 1.234], rtol=0)

    def test_precision_above_range_skips_adjustment(self):
        """precision=7 超出 [1,6] 范围，应跳过精度调整"""
        cfg = _make_config()
        df = DatFile.from_str(cfg, _ASCII_DATA, analog_precision=7)
        assert df is not None
        np.testing.assert_allclose(df.iloc[:, 2].to_numpy(), [1.234, 1.234], rtol=0)

    def test_precision_rounds_up(self):
        """验证四舍五入向上"""
        cfg = _make_config()
        # 原始 1235 -> 1.235，precision=2 应为 1.24
        data = "1,0,1235\n2,1000,1235\n"
        df = DatFile.from_str(cfg, data, analog_precision=2)
        assert df is not None
        np.testing.assert_allclose(df.iloc[:, 2].to_numpy(), [1.24, 1.24], rtol=0)


class TestAnalogPrecisionFallback:
    """验证非法精度输入在 __post_init__ 中回退到默认值 3"""

    def test_invalid_string_falls_back_to_default(self):
        cfg = _make_config()
        dat = DatFile(config=cfg, analog_precision="abc")  # type: ignore[arg-type]
        assert dat.analog_precision == 3

    def test_none_falls_back_to_default(self):
        cfg = _make_config()
        dat = DatFile(config=cfg, analog_precision=None)  # type: ignore[arg-type]
        assert dat.analog_precision == 3

    def test_float_string_converted_to_int(self):
        cfg = _make_config()
        dat = DatFile(config=cfg, analog_precision="2")  # type: ignore[arg-type]
        assert dat.analog_precision == 2
