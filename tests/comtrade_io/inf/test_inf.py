import tempfile
from pathlib import Path

import pytest

from comtrade_io.inf import InfInfo


def test_parse_inf_basic():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
# Sample INF
Manufacturer=ACME Corp
Model=PowerMeter 3000
Serial_Number=SN12345
CT_Ratio=100/1
PT_Ratio=110/1
Frequency=60
SamplingRate=2048
Software_Version=1.2.3
""".strip(),
            encoding="utf-8"
        )
        inf = InfInfo.from_file(p)
        assert inf.manufacturer is not None
        assert inf.manufacturer == "ACME Corp"
        assert inf.model == "PowerMeter 3000"
        assert inf.serial_number == "SN12345"
        assert inf.ct_ratio == "100/1"
        assert inf.pt_ratio == "110/1"
        assert inf.frequency == 60
        assert inf.sampling_rate == 2048
        assert inf.software_version == "1.2.3"


def test_missing_fields():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text("Manufacturer=ACME", encoding="utf-8")
        inf = InfInfo.from_file(p)
        assert inf.manufacturer == "ACME"
        assert inf.model is None


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        InfInfo.from_file(Path("no_such.inf"))


def test_comments_and_spaces():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text("""
# comment line
Manufacturer = ACME
; another comment
Model: Meter X
""".strip(), encoding="utf-8")
        inf = InfInfo.from_file(p)
        assert inf.manufacturer == "ACME"
        assert inf.model == "Meter X"
