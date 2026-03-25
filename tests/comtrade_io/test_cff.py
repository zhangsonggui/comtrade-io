#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests/comtrade_io/test_cff.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Unit and integration tests for CFF (Combined File Format) support.

Run with:  pytest tests/comtrade_io/test_cff.py -v
"""

from __future__ import annotations

import io
import struct
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

import pytest

from comtrade_io.cff_splitter import CffSections, split_cff


# ── Shared test fixtures ──────────────────────────────────────────────────

MINIMAL_CFG = textwrap.dedent("""\
    TestStation,REL_001,2013
    3,2A,1D
    1,Ia,,A,A,,1,0,-32768,32767,1,1,S
    2,Ib,,A,A,,1,0,-32768,32767,1,1,S
    1,BRK1,,,,0
    50.0
    1
    1000,3
    01/01/2020,00:00:00.000000
    01/01/2020,00:00:00.002000
    ASCII
    1
""")

MINIMAL_DAT_ASCII = "1,0,100,200,0\n2,1000,110,210,0\n3,2000,120,220,1\n"

INF_CONTENT = "Manufacturer=ACME\nModel=REL_001\n"
HDR_CONTENT = "Recorder: TEST_IED\nFirmware: v2.1\n"


def _make_cff_text(include_inf: bool = False, include_hdr: bool = False) -> str:
    parts = []
    if include_hdr:
        parts.append("--- file type: HDR ---\n")
        parts.append(HDR_CONTENT)
    if include_inf:
        parts.append("--- file type: INF ---\n")
        parts.append(INF_CONTENT)
    parts.append("--- file type: CFG ---\n")
    parts.append(MINIMAL_CFG)
    parts.append("--- file type: DAT ASCII: 0 ---\n")
    parts.append(MINIMAL_DAT_ASCII)
    return "".join(parts)


def _make_cff_binary() -> bytes:
    """
    Build a minimal FLOAT32 CFF.  Each sample: uint32 index, uint32 ts,
    2× float32 analog, 1× uint16 digital word = 18 bytes × 3 samples.
    """
    samples = [(1, 0, 1.0, 2.0, 0), (2, 1000, 1.1, 2.1, 0), (3, 2000, 1.2, 2.2, 1)]
    dat_bytes = b"".join(struct.pack("<IIffH", *s) for s in samples)
    header = (
        f"--- file type: CFG ---\n{MINIMAL_CFG}"
        f"--- file type: DAT FLOAT32: {len(dat_bytes)} ---\n"
    ).encode("utf-8")
    return header + dat_bytes


def _write_tmp_cff(content: str) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".cff", mode="wb", delete=False) as f:
        f.write(content.encode("utf-8"))
        return Path(f.name)


def _write_tmp_cff_bytes(content: bytes) -> Path:
    with tempfile.NamedTemporaryFile(suffix=".cff", mode="wb", delete=False) as f:
        f.write(content)
        return Path(f.name)


# ── CffSections / split_cff unit tests ───────────────────────────────────

class TestCffSplitterAscii:

    def test_cfg_section_parsed(self):
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            sec = split_cff(tmp)
            assert "TestStation" in sec.cfg
            assert "2013" in sec.cfg
        finally:
            tmp.unlink()

    def test_dat_ascii_section_parsed(self):
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            sec = split_cff(tmp)
            assert sec.dat_encoding == "ASCII"
            assert sec.dat_text is not None
            assert sec.dat_bytes is None
            assert "1,0,100,200" in sec.dat_text
        finally:
            tmp.unlink()

    def test_optional_inf_absent(self):
        tmp = _write_tmp_cff(_make_cff_text(include_inf=False))
        try:
            assert split_cff(tmp).inf is None
        finally:
            tmp.unlink()

    def test_optional_inf_present(self):
        tmp = _write_tmp_cff(_make_cff_text(include_inf=True))
        try:
            sec = split_cff(tmp)
            assert sec.inf is not None
            assert "ACME" in sec.inf
        finally:
            tmp.unlink()

    def test_optional_hdr_present(self):
        tmp = _write_tmp_cff(_make_cff_text(include_hdr=True))
        try:
            sec = split_cff(tmp)
            assert sec.hdr is not None
            assert "TEST_IED" in sec.hdr
        finally:
            tmp.unlink()

    def test_cfg_stream_is_string_io(self):
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            sec = split_cff(tmp)
            stream = sec.cfg_stream()
            assert isinstance(stream, io.StringIO)
            assert "TestStation" in stream.readline()
        finally:
            tmp.unlink()

    def test_dat_stream_ascii_is_string_io(self):
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            assert isinstance(split_cff(tmp).dat_stream(), io.StringIO)
        finally:
            tmp.unlink()

    def test_missing_cfg_raises(self):
        tmp = _write_tmp_cff("--- file type: DAT ASCII: 0 ---\n1,0,1,2\n")
        try:
            with pytest.raises(ValueError, match="CFG"):
                split_cff(tmp)
        finally:
            tmp.unlink()

    def test_missing_dat_raises(self):
        tmp = _write_tmp_cff(f"--- file type: CFG ---\n{MINIMAL_CFG}")
        try:
            with pytest.raises(ValueError, match="DAT"):
                split_cff(tmp)
        finally:
            tmp.unlink()

    def test_case_insensitive_sentinels(self):
        mixed = (
            "--- File Type: CFG ---\n"
            + MINIMAL_CFG
            + "--- file type: DAT ascii: 0 ---\n"
            + MINIMAL_DAT_ASCII
        )
        tmp = _write_tmp_cff(mixed)
        try:
            sec = split_cff(tmp)
            assert sec.cfg
            assert sec.dat_text
        finally:
            tmp.unlink()


class TestCffSplitterBinary:

    def test_binary_dat_stored_as_bytes(self):
        tmp = _write_tmp_cff_bytes(_make_cff_binary())
        try:
            sec = split_cff(tmp)
            assert sec.dat_encoding == "FLOAT32"
            assert sec.dat_bytes is not None
            assert sec.dat_text is None
        finally:
            tmp.unlink()

    def test_binary_dat_byte_count_correct(self):
        tmp = _write_tmp_cff_bytes(_make_cff_binary())
        try:
            # 3 samples × (uint32 + uint32 + float32 + float32 + uint16) = 3 × 18 = 54
            assert len(split_cff(tmp).dat_bytes) == 54
        finally:
            tmp.unlink()

    def test_dat_stream_binary_is_bytes_io(self):
        tmp = _write_tmp_cff_bytes(_make_cff_binary())
        try:
            assert isinstance(split_cff(tmp).dat_stream(), io.BytesIO)
        finally:
            tmp.unlink()

    def test_float32_first_sample_values(self):
        tmp = _write_tmp_cff_bytes(_make_cff_binary())
        try:
            data = split_cff(tmp).dat_bytes
            sn, ts, a1, a2, dig = struct.unpack_from("<IIffH", data, 0)
            assert sn == 1
            assert ts == 0
            assert abs(a1 - 1.0) < 1e-5
            assert abs(a2 - 2.0) < 1e-5
        finally:
            tmp.unlink()


# ── Configure.from_str round-trip ────────────────────────────────────────

class TestConfigureFromStr:
    """Verify that the CFG section parses correctly via the existing from_str."""

    def test_station_name(self):
        from comtrade_io.cfg import Configure
        cfg = Configure.from_str(MINIMAL_CFG)
        assert cfg.header.station == "TestStation"

    def test_analog_count(self):
        from comtrade_io.cfg import Configure
        cfg = Configure.from_str(MINIMAL_CFG)
        assert cfg.channel_num.analog == 2

    def test_digital_count(self):
        from comtrade_io.cfg import Configure
        cfg = Configure.from_str(MINIMAL_CFG)
        assert cfg.channel_num.digital == 1  # 1D declared in header


# ── DataContent.from_str unit tests ──────────────────────────────────────

class TestDataContentFromStr:

    def _cfg(self):
        from comtrade_io.cfg import Configure
        return Configure.from_str(MINIMAL_CFG)

    def test_ascii_row_count(self):
        from comtrade_io.data import DataContent
        dc = DataContent.from_str(cfg=self._cfg(), dat_str=MINIMAL_DAT_ASCII)
        assert len(dc.data) == 3

    def test_ascii_column_count(self):
        from comtrade_io.data import DataContent
        dc = DataContent.from_str(cfg=self._cfg(), dat_str=MINIMAL_DAT_ASCII)
        # 2 header cols + 2 analog + 1 digital = 5
        assert dc.data.shape[1] == 5

    def test_raises_without_data(self):
        from comtrade_io.data import DataContent
        with pytest.raises(ValueError):
            DataContent.from_str(cfg=self._cfg())

    def test_raises_with_both_str_and_bytes(self):
        from comtrade_io.data import DataContent
        with pytest.raises(ValueError):
            DataContent.from_str(cfg=self._cfg(), dat_str="x", dat_bytes=b"x")


# ── InfInfo.from_stream unit test ─────────────────────────────────────────

class TestInfInfoFromStream:

    def test_parses_manufacturer(self):
        from comtrade_io.inf.inf import InfInfo
        info = InfInfo.from_stream(io.StringIO(INF_CONTENT))
        assert info.manufacturer == "ACME"

    def test_parses_model(self):
        from comtrade_io.inf.inf import InfInfo
        info = InfInfo.from_stream(io.StringIO(INF_CONTENT))
        assert info.model == "REL_001"

    def test_empty_stream_returns_empty_instance(self):
        from comtrade_io.inf.inf import InfInfo
        info = InfInfo.from_stream(io.StringIO(""))
        assert info.manufacturer is None
        assert info.data == {}


# ── Integration: Comtrade.from_file() with .cff ───────────────────────────

class TestComtradeFromCff:

    def test_from_file_detects_cff(self):
        from comtrade_io import Comtrade
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            wave = Comtrade.from_file(str(tmp))
            assert wave is not None
        finally:
            tmp.unlink()

    def test_cfg_station_name(self):
        from comtrade_io import Comtrade
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            assert Comtrade.from_file(str(tmp)).cfg.header.station == "TestStation"
        finally:
            tmp.unlink()

    def test_analog_channel_count(self):
        from comtrade_io import Comtrade
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            assert len(Comtrade.from_file(str(tmp)).cfg.analogs) == 2
        finally:
            tmp.unlink()

    def test_data_frame_row_count(self):
        from comtrade_io import Comtrade
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            assert len(Comtrade.from_file(str(tmp)).get_data()) == 3
        finally:
            tmp.unlink()

    def test_inf_populated_when_present(self):
        # Comtrade doesn't expose an .inf field — INF parsing is tested
        # directly in TestInfInfoFromStream. Here we just verify that a CFF
        # with an embedded INF section still loads without error.
        from comtrade_io import Comtrade
        tmp = _write_tmp_cff(_make_cff_text(include_inf=True))
        try:
            wave = Comtrade.from_file(str(tmp))
            assert wave is not None
            assert len(wave.get_data()) == 3  # data still intact
        finally:
            tmp.unlink()

    def test_hdr_populated_when_present(self):
        # Comtrade doesn't expose an .hdr field — HDR has no structured parser.
        # Verify that a CFF with an embedded HDR section still loads without error.
        from comtrade_io import Comtrade
        tmp = _write_tmp_cff(_make_cff_text(include_hdr=True))
        try:
            wave = Comtrade.from_file(str(tmp))
            assert wave is not None
            assert len(wave.get_data()) == 3  # data still intact
        finally:
            tmp.unlink()

    def test_from_cff_directly(self):
        from comtrade_io import Comtrade
        tmp = _write_tmp_cff(_make_cff_text())
        try:
            wave = Comtrade.from_cff(str(tmp))
            assert wave is not None
            assert wave.cfg.header.station == "TestStation"
        finally:
            tmp.unlink()

    def test_none_returned_for_missing_cff(self):
        from comtrade_io import Comtrade
        assert Comtrade.from_cff("/nonexistent/path/file.cff") is None
