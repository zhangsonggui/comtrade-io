"""
Module with tests of our main Comtrade reader.

TestCffReading - design decisions
Round-trip approach instead of a static .cff test file. The existing test data is binary format (binary_1999.cfg).
Rather than shipping a separate .cff file or converting binary to CFF (which would require the binary parser to be correct before the CFF parser can even be tested),
we serialise the already-loaded comtrade fixture to ASCII CFF using Configure.__str__() and DataFrame.to_csv() — both already trusted by the other passing tests — then read it back.
This means a failure can only come from the CFF path itself.
scope="class" fixture for cff_wave. The round-trip file is created once per class, not once per test — same pattern as the scope="session" comtrade fixture.
The CFF file lands in pytest's tmp_path_factory directory and is cleaned up automatically.

10 tests covering four areas:
* test_cff_loads_successfully — the most basic smoke test
* test_cff_station_name / analog_count / digital_count / sample_count — metadata round-trips correctly
* test_cff_first_analog_channel_data / all_analog_channels_data — analog values survive the ASCII serialisation within < 0.01 tolerance (same threshold as the existing tests)
* test_cff_all_digital_channels_data — digital channels must be bit-exact
* test_cff_with_inf_section_loads / test_cff_with_hdr_section_loads — optional sections don't break loading; use tmp_path (function scope) since they're self-contained and
guard with pytest.skip if the data file is absent

Fixed tests:
tests/comtrade_io/test_comtrade.py:376 (TestCffReading.test_cff_first_analog_channel_data)
np.float64(84.65168881542895) != 0.01
Expected :0.01
Actual   :np.float64(84.65168881542895)

tests/comtrade_io/test_comtrade.py:382 (TestCffReading.test_cff_all_analog_channels_data)
np.float64(84.65168881542895) != 0.01
Expected :0.01
Actual   :np.float64(84.65168881542895)

REASON: cff_wave channel 1 shows values like -0.16 while comtrade shows -20.5. The ratio is exactly the multiplier/offset scaling
— the original comtrade data has already been scaled (multiplier × raw + offset applied in _apply_type_mapping_and_scaling), but when we write it to CSV and read it back as a CFF,
DataContent.from_str applies the scaling again.
FIX: write the raw (unscaled) data to the CFF, not the already-scaled DataFrame. We need to reverse-scale before writing, or better — serialize the raw integer values.
Looking at the existing _write_ascii_dat_file, it writes self.data directly (the scaled data) to CSV for the save_comtrade path too, which would have the same bug.
The correct approach for our round-trip test is to inverse-scale before writing

Insights:
* Root cause: comtrade.dat.data holds scaled values — DataContent._apply_type_mapping_and_scaling() has already applied raw × multiplier + offset.
  Writing those scaled floats to the CSV and then reading them back through DataContent.from_str() applied the scaling a second time, producing values off by the multiplier factor (~84 in this case).
* Fix: before writing the CSV, reverse the scaling with raw = (scaled - offset) / multiplier. The same fix was applied consistently to all three places in the test class
  that build a CFF from scratch (cff_wave fixture, test_cff_with_inf_section_loads, test_cff_with_hdr_section_loads).
* This is also a useful signal about save_comtrade() / _write_ascii_dat_file() in the main codebase — it writes the scaled DataFrame directly,
  which means a save→reload round-trip via cfg+dat would have the same double-scaling bug. Worth a separate look.
"""
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
        assert comtrade.cfg.channel_num.digital == 192
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
        assert line.lin_len == 9.75
        assert line.bran_num.value == 1
        assert len(line.currents) == line.bran_num.value
        assert line.rx.r0 == 0.062
        assert line.rx.r1 == 0.021

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
        assert bus.v_rtg_snd_pos.value == "BUS"

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
        assert trans.pwr_rtg == 0
        assert len(trans.transWinds) == 2

    def test_get_transformer_winding(self, comtrade):
        """测试变压器绕组信息"""
        trans = comtrade.get_transformer("1号主变")
        trans_h = trans.transWinds[0]
        assert trans_h.location.value == "high"
        assert trans_h.v_rtg == 0
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
        assert trans_h.igap.zgap_idx == 0
        assert trans_h.igap.zsgap_idx == 0

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
        digital_count = comtrade.cfg.channel_num.digital
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


class TestCffReading:
    """
    Test CFF (Combined File Format) round-trip using the real binary_1999 data.

    Strategy: serialise the already-loaded Comtrade to a temporary ASCII CFF,
    read it back, then assert that the key metadata and sample values are
    identical.  This exercises the full CFF path (cff_splitter → Configure.from_str
    → DataContent.from_str) against real-world data without requiring a separate
    test data file.
    """

    @pytest.fixture(scope="class")
    def cff_wave(self, comtrade, tmp_path_factory):
        """
        Build an ASCII CFF from the real comtrade fixture and load it back.
        Stored at class scope so it is created once and reused across all
        tests in this class.

        We must write raw (unscaled) analog values to the CFF, because
        DataContent.from_str() applies multiplier/offset scaling on read —
        the same as reading from a .dat file.  The already-scaled DataFrame
        in comtrade.dat.data must therefore be inverse-scaled before writing.
        """
        import io
        import numpy as np

        tmp_dir = tmp_path_factory.mktemp("cff")
        cff_path = tmp_dir / "binary_1999.cff"

        cfg_str = str(comtrade.cfg)

        # Inverse-scale: raw = (scaled - offset) / multiplier
        df_raw = comtrade.dat.data.copy()
        analog_list = list(comtrade.cfg.analogs.values())
        multipliers = np.array([a.multiplier for a in analog_list])
        offsets     = np.array([a.offset     for a in analog_list])
        analog_cols = list(range(2, 2 + comtrade.cfg.channel_num.analog))
        df_raw.iloc[:, analog_cols] = (
            (df_raw.iloc[:, analog_cols].values - offsets) / multipliers
        )

        dat_buf = io.StringIO()
        df_raw.to_csv(dat_buf, header=False, index=False)
        dat_str = dat_buf.getvalue()

        cff_content = (
            "--- file type: CFG ---\n"
            + cfg_str + "\n"
            + "--- file type: DAT ASCII: 0 ---\n"
            + dat_str
        )
        cff_path.write_text(cff_content, encoding="utf-8")

        return Comtrade.from_file(str(cff_path))

    # ── Metadata ────────────────────────────────────────────────────────

    def test_cff_loads_successfully(self, cff_wave):
        """from_file() on a .cff path must return a Comtrade instance."""
        assert cff_wave is not None

    def test_cff_station_name(self, cff_wave, comtrade):
        assert cff_wave.cfg.header.station == comtrade.cfg.header.station

    def test_cff_analog_channel_count(self, cff_wave, comtrade):
        assert cff_wave.cfg.channel_num.analog == comtrade.cfg.channel_num.analog

    def test_cff_digital_channel_count(self, cff_wave, comtrade):
        assert cff_wave.cfg.channel_num.digital == comtrade.cfg.channel_num.digital

    def test_cff_sample_count(self, cff_wave, comtrade):
        assert len(cff_wave.get_data()) == len(comtrade.get_data())

    # ── Analog channel data fidelity ────────────────────────────────────

    def test_cff_first_analog_channel_data(self, cff_wave, comtrade):
        """First analog channel values must be numerically identical."""
        actual   = cff_wave.get_data().iloc[:, 2].values
        expected = comtrade.get_data().iloc[:, 2].values
        assert np.max(np.abs(actual - expected)) < 0.01

    def test_cff_all_analog_channels_data(self, cff_wave, comtrade):
        """All analog channels must round-trip within floating-point tolerance."""
        analog_count = comtrade.cfg.channel_num.analog
        df_cff      = cff_wave.get_data()
        df_orig     = comtrade.get_data()
        for ch_idx in range(analog_count):
            col = ch_idx + 2
            max_diff = np.max(np.abs(df_cff.iloc[:, col].values - df_orig.iloc[:, col].values))
            assert max_diff < 0.01, f"Analog channel {ch_idx + 1} mismatch (max diff {max_diff})"

    # ── Digital channel data fidelity ───────────────────────────────────

    def test_cff_all_digital_channels_data(self, cff_wave, comtrade):
        """All digital channels must round-trip exactly."""
        analog_count   = comtrade.cfg.channel_num.analog
        digital_count  = comtrade.cfg.channel_num.digital
        df_cff  = cff_wave.get_data()
        df_orig = comtrade.get_data()
        for ch_idx in range(digital_count):
            col = analog_count + 2 + ch_idx
            assert np.array_equal(
                df_cff.iloc[:, col].values,
                df_orig.iloc[:, col].values,
            ), f"Digital channel {ch_idx + 1} mismatch"

    # ── Optional sections (smoke tests) ─────────────────────────────────

    def test_cff_with_inf_section_loads(self, tmp_path):
        """A CFF with an embedded INF section must load without error."""
        if not CFG_FILE.exists():
            pytest.skip("binary_1999.cfg not available")

        import io
        import numpy as np

        orig = Comtrade.from_file(str(CFG_FILE))
        inf_block = "Manufacturer=TestIED\nModel=REL001\n"

        df_raw = orig.dat.data.copy()
        analog_list  = list(orig.cfg.analogs.values())
        multipliers  = np.array([a.multiplier for a in analog_list])
        offsets      = np.array([a.offset     for a in analog_list])
        analog_cols  = list(range(2, 2 + orig.cfg.channel_num.analog))
        df_raw.iloc[:, analog_cols] = (
            (df_raw.iloc[:, analog_cols].values - offsets) / multipliers
        )
        dat_buf = io.StringIO()
        df_raw.to_csv(dat_buf, header=False, index=False)

        cff_content = (
            "--- file type: INF ---\n"
            + inf_block
            + "--- file type: CFG ---\n"
            + str(orig.cfg) + "\n"
            + "--- file type: DAT ASCII: 0 ---\n"
            + dat_buf.getvalue()
        )
        cff_path = tmp_path / "with_inf.cff"
        cff_path.write_text(cff_content, encoding="utf-8")

        wave = Comtrade.from_file(str(cff_path))
        assert wave is not None
        assert len(wave.get_data()) == len(orig.get_data())

    def test_cff_with_hdr_section_loads(self, tmp_path):
        """A CFF with an embedded HDR section must load without error."""
        if not CFG_FILE.exists():
            pytest.skip("binary_1999.cfg not available")

        import io
        import numpy as np

        orig = Comtrade.from_file(str(CFG_FILE))
        hdr_block = "Recorder: TEST_IED\nFirmware: v2.1\n"

        df_raw = orig.dat.data.copy()
        analog_list  = list(orig.cfg.analogs.values())
        multipliers  = np.array([a.multiplier for a in analog_list])
        offsets      = np.array([a.offset     for a in analog_list])
        analog_cols  = list(range(2, 2 + orig.cfg.channel_num.analog))
        df_raw.iloc[:, analog_cols] = (
            (df_raw.iloc[:, analog_cols].values - offsets) / multipliers
        )
        dat_buf = io.StringIO()
        df_raw.to_csv(dat_buf, header=False, index=False)

        cff_content = (
            "--- file type: HDR ---\n"
            + hdr_block
            + "--- file type: CFG ---\n"
            + str(orig.cfg) + "\n"
            + "--- file type: DAT ASCII: 0 ---\n"
            + dat_buf.getvalue()
        )
        cff_path = tmp_path / "with_hdr.cff"
        cff_path.write_text(cff_content, encoding="utf-8")

        wave = Comtrade.from_file(str(cff_path))
        assert wave is not None
        assert len(wave.get_data()) == len(orig.get_data())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
