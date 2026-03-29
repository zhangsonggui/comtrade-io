from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from comtrade_io.comtrade import Comtrade

DATA_DIR = Path(__file__).parent.parent / "data"
CFG_FILE = DATA_DIR / "binary_1999.cfg"
CSV_FILE = DATA_DIR / "binary_1999.csv"


@pytest.fixture(scope="session")
def comtrade():
    """Global Comtrade instance for all tests"""
    return Comtrade.from_file(file_name=CFG_FILE)


@pytest.fixture(scope="session")
def expected_df():
    """从CSV文件加载期望数据（跳过标题行）"""
    df = pd.read_csv(CSV_FILE, header=None, encoding="gbk", skiprows=1, low_memory=False)
    return df


class TestComtradeInitialization:
    """测试Comtrade类初始化"""

    def test_comtrade_initialization(self, comtrade):
        """测试Comtrade类初始化"""
        assert comtrade.file.cfg_path.path == CFG_FILE
        assert comtrade.cfg.header.station == "GHBZ"
        assert comtrade.cfg.channel_num.analog == 96
        assert comtrade.cfg.channel_num.status == 192
        assert comtrade.cfg.data_type.value == "BINARY"

    def test_data_loaded(self, comtrade):
        """测试数据已正确加载"""
        df = comtrade.get_data()
        assert df is not None
        assert df.shape[0] == 45600
        assert df.shape[1] == 290


class TestGetLine:
    """测试获取线路"""

    def test_get_line_info(self, comtrade):
        """测试获取线路基本信息"""
        line = comtrade.get_line("ghx")
        assert line.index == 3
        assert line.name == "ghx"
        assert line.line_length == 9.75
        assert line.bran_num.value == 1
        assert len(line.currents) == line.bran_num.value
        assert line.impedance.r0 == 0.062
        assert line.impedance.r1 == 0.021

    def test_get_line_currents(self, comtrade):
        """测试线路电流通道"""
        line = comtrade.get_line("ghx")
        assert line.currents[0].idx == 1
        assert line.currents[0].dir.name == "POS"
        assert line.currents[0].ia.index == 25
        assert line.currents[0].ib.index == 26
        assert line.currents[0].ic.index == 27
        assert line.currents[0].i0.index == 28

    def test_get_line_voltages(self, comtrade):
        """测试线路电压通道"""
        line = comtrade.get_line("ghx")
        assert line.buses[0].voltage.ua.index == 1
        assert line.buses[0].voltage.ub.index == 2
        assert line.buses[0].voltage.uc.index == 3
        assert line.buses[0].voltage.un.index == 4

    def test_get_line_current_data(self, comtrade, expected_df):
        """测试线路电流通道数据"""
        line = comtrade.get_line("ghx")
        for current in line.currents:
            col_idx = current.ia.index + 2
            actual = comtrade.get_data().iloc[:, col_idx].values
            expected = expected_df.iloc[:, col_idx].values.astype(float)
            max_diff = np.max(np.abs(actual - expected))
            assert max_diff < 0.01, f"通道{current.ia.index}数据不匹配"

    def test_get_line_voltage_data(self, comtrade, expected_df):
        """测试线路电压通道数据"""
        line = comtrade.get_line("ghx")
        for bus in line.buses:
            for ch in [bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.un]:
                if ch.index is not None:
                    col_idx = ch.index + 2
                    actual = comtrade.get_data().iloc[:, col_idx].values
                    expected = expected_df.iloc[:, col_idx].values.astype(float)
                    max_diff = np.max(np.abs(actual - expected))
                    assert max_diff < 0.01, f"通道{ch.index}数据不匹配"


class TestGetBus:
    """测试获取母线"""

    def test_get_bus_info(self, comtrade):
        """测试获取母线基本信息"""
        bus = comtrade.get_bus("220kV母线U")
        assert bus.index == 1
        assert bus.name == "220kV母线U"
        assert bus.tv_install_site.value == "BUS"

    def test_get_bus_voltages(self, comtrade):
        """测试母线电压通道"""
        bus = comtrade.get_bus("220kV母线U")
        assert bus.voltage.ua.index == 1
        assert bus.voltage.ub.index == 2
        assert bus.voltage.uc.index == 3
        assert bus.voltage.un.index == 4

    def test_get_bus_voltage_data(self, comtrade, expected_df):
        """测试母线电压通道数据"""
        bus = comtrade.get_bus("220kV母线U")
        for ch in [bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.un]:
            if ch.index is not None:
                col_idx = ch.index + 2
                actual = comtrade.get_data().iloc[:, col_idx].values
                expected = expected_df.iloc[:, col_idx].values.astype(float)
                max_diff = np.max(np.abs(actual - expected))
                assert max_diff < 0.01, f"通道{ch.index}数据不匹配"


class TestGetTransformer:
    """测试获取变压器"""

    def test_get_transformer_info(self, comtrade):
        """测试获取变压器基本信息"""
        trans = comtrade.get_transformer("1号主变")
        assert trans.index == 1
        assert trans.name == "1号主变"
        assert trans.capacity == 0
        assert len(trans.transWinds) == 2

    def test_get_transformer_winding(self, comtrade):
        """测试变压器绕组信息"""
        trans = comtrade.get_transformer("1号主变")
        trans_h = trans.transWinds[0]
        assert trans_h.trans_wind_location.value == "high"
        assert trans_h.rated_voltage == 0
        assert trans_h.bran_num == len(trans_h.currents)
        assert trans_h.currents[0].idx == 1
        assert trans_h.currents[0].dir.value == "pos"

    def test_get_transformer_currents(self, comtrade):
        """测试变压器电流通道"""
        trans = comtrade.get_transformer("1号主变")
        trans_h = trans.transWinds[0]
        assert trans_h.currents[0].ia.index == 21
        assert trans_h.currents[0].ib.index == 22
        assert trans_h.currents[0].ic.index == 23
        assert trans_h.currents[0].i0.index == 24

    def test_get_transformer_voltages(self, comtrade):
        """测试变压器电压通道"""
        trans = comtrade.get_transformer("1号主变")
        trans_h = trans.transWinds[0]
        assert trans_h.voltage.ua.index == 1
        assert trans_h.voltage.ub.index == 2
        assert trans_h.voltage.uc.index == 3
        assert trans_h.voltage.un.index == 4
        assert trans_h.igap.zgap is None
        assert trans_h.igap.zsgap is None

    def test_get_transformer_current_data(self, comtrade, expected_df):
        """测试变压器电流通道数据"""
        trans = comtrade.get_transformer("1号主变")
        for winding in trans.transWinds:
            for current in winding.currents:
                for ch in [current.ia, current.ib, current.ic, current.i0]:
                    if ch.index is not None:
                        col_idx = ch.index + 2
                        actual = comtrade.get_data().iloc[:, col_idx].values
                        expected = expected_df.iloc[:, col_idx].values.astype(float)
                        max_diff = np.max(np.abs(actual - expected))
                        assert max_diff < 0.01, f"通道{ch.index}数据不匹配"

    def test_get_transformer_voltage_data(self, comtrade, expected_df):
        """测试变压器电压通道数据"""
        trans = comtrade.get_transformer("1号主变")
        for winding in trans.transWinds:
            for ch in [winding.voltage.ua, winding.voltage.ub, winding.voltage.uc, winding.voltage.un]:
                if ch.index is not None:
                    col_idx = ch.index + 2
                    actual = comtrade.get_data().iloc[:, col_idx].values
                    expected = expected_df.iloc[:, col_idx].values.astype(float)
                    max_diff = np.max(np.abs(actual - expected))
                    assert max_diff < 0.01, f"通道{ch.index}数据不匹配"


class TestGetAnalogChannel:
    """测试获取模拟量通道"""

    def test_get_analog_channel_info(self, comtrade):
        """测试获取模拟量通道基本信息"""
        analog = comtrade.get_analog_channel(1)
        assert analog.index == 1
        assert analog.name == "220kV母线_Ua"

    def test_get_analog_channel_data(self, comtrade, expected_df):
        """测试模拟量通道数据"""
        analog = comtrade.get_analog_channel(1)
        col_idx = 2
        actual = analog.data
        expected = expected_df.iloc[:, col_idx].values.astype(float)
        max_diff = np.max(np.abs(actual - expected))
        assert max_diff < 0.01, f"通道1数据不匹配，最大差异: {max_diff}"

    def test_get_all_analog_channels_data(self, comtrade, expected_df):
        """测试所有模拟量通道数据"""
        analog_count = comtrade.cfg.channel_num.analog
        for ch_idx in range(1, analog_count + 1):
            analog = comtrade.get_analog_channel(ch_idx)
            col_idx = ch_idx + 1
            actual = analog.data
            expected = expected_df.iloc[:, col_idx].values.astype(float)
            max_diff = np.max(np.abs(actual - expected))
            assert max_diff < 0.01, f"通道{ch_idx}数据不匹配，最大差异: {max_diff}"

    def test_analog_channel_has_data(self, comtrade):
        """测试模拟量通道有数据"""
        analog = comtrade.get_analog_channel(1)
        assert analog.data is not None
        assert len(analog.data) == 45600


class TestGetStatusChannel:
    """测试获取状态量通道"""

    def test_get_status_channel_info(self, comtrade):
        """测试获取状态量通道基本信息"""
        status = comtrade.get_status_channel(1)
        assert status.index == 1

    def test_get_status_channel_data(self, comtrade, expected_df):
        """测试状态量通道数据"""
        status = comtrade.get_status_channel(1)
        analog_count = comtrade.cfg.channel_num.analog
        col_idx = analog_count + 2
        actual = status.data
        expected = expected_df.iloc[:, col_idx].values.astype(int)
        assert np.array_equal(actual, expected), "通道1数据不匹配"

    def test_get_all_status_channels_data(self, comtrade, expected_df):
        """测试所有状态量通道数据"""
        analog_count = comtrade.cfg.channel_num.analog
        digital_count = comtrade.cfg.channel_num.status
        for ch_idx in range(1, digital_count + 1):
            status = comtrade.get_status_channel(ch_idx)
            col_idx = analog_count + ch_idx + 1
            actual = status.data
            expected = expected_df.iloc[:, col_idx].values.astype(int)
            assert np.array_equal(actual, expected), f"通道{ch_idx}数据不匹配"


class TestDataConsistency:
    """测试数据一致性"""

    def test_all_lines_have_data(self, comtrade):
        """测试所有线路都有数据"""
        for line in comtrade.lines:
            loaded_line = comtrade.get_line(line.name)
            assert loaded_line is not None
            for current in loaded_line.currents:
                assert current.ia.data is not None
                assert current.ib.data is not None
                assert current.ic.data is not None
                assert current.i0.data is not None

    def test_all_buses_have_data(self, comtrade):
        """测试所有母线都有数据"""
        for bus in comtrade.buses:
            loaded_bus = comtrade.get_bus(bus.name)
            assert loaded_bus is not None
            for ch in [loaded_bus.voltage.ua, loaded_bus.voltage.ub, loaded_bus.voltage.uc, loaded_bus.voltage.un]:
                if ch.index is not None:
                    col_idx = ch.index + 2
                    assert ch.data is not None

    def test_all_transformers_have_data(self, comtrade):
        """测试所有变压器都有数据"""
        for trans in comtrade.transformers:
            loaded_trans = comtrade.get_transformer(trans.name)
            assert loaded_trans is not None
            for winding in loaded_trans.transWinds:
                for current in winding.currents:
                    for ch in [current.ia, current.ib, current.ic, current.i0]:
                        if ch.index is not None:
                            col_idx = ch.index + 2
                            assert ch.data is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
