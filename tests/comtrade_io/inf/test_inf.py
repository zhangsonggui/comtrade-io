import tempfile
from pathlib import Path

import pytest

from comtrade_io.inf import Information


def test_parse_inf_basic():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
[Public Record_Information]
Source=Test Source
Record_Information=
Location=Test Location

[Public File_Description]
Station_Name=Test Station
Recording_Device_ID=Device1
Revision_Year=1999
Total_Channel_Count=10
Analog_Channel_Count=5
Status_Channel_Count=5
Line_Frequency=50
Sample_Rate_Count=1
Sample_Rate_#1=4000
End_Sample_Rate_#1=4000
File_Start_Time=01/01/2024,00:00:00.000000
Trigger_Time=01/01/2024,00:00:01.000000
File_Type=BINARY
Time_Multiplier=1
            """.strip(),
            encoding="utf-8"
        )
        inf = Information.from_file(p)
        assert inf.get_record_information() is not None
        assert inf.get_file_description() is not None
        assert inf.get_record_information().Source == "Test Source"
        assert inf.get_file_description().Station_Name == "Test Station"


def test_analog_channels():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
[Public Analog_Channel_#1]
Channel_ID=1
Phase_ID=A
Monitored_Component=TCTR$MX$Amp$
Channel_Units=A
Channel_Multiplier=1.0

[Public Analog_Channel_#2]
Channel_ID=2
Phase_ID=B
            """.strip(),
            encoding="utf-8"
        )
        inf = Information.from_file(p)
        channels = inf.get_analog_channels()
        assert len(channels) == 2
        assert channels[0].Channel_ID == "1"
        assert channels[0].Phase_ID == "A"
        assert channels[1].Channel_ID == "2"


def test_zyhd_sections():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
[ZYHD Bus_#1]
Name=Bus1

[ZYHD Line_#1]
Name=Line1

[ZYHD Transformer_#1]
Name=Transformer1
            """.strip(),
            encoding="utf-8"
        )
        inf = Information.from_file(p)
        buses = inf.get_buses()
        lines = inf.get_lines()
        transformers = inf.get_transformers()
        assert len(buses) == 1
        assert len(lines) == 1
        assert len(transformers) == 1


def test_serialization():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
[Public Record_Information]
Source=Test

[Public Analog_Channel_#1]
Channel_ID=1
            """.strip(),
            encoding="utf-8"
        )
        inf1 = Information.from_file(p)
        output = inf1.to_string()

        inf2 = Information()
        inf2.parse(output)

        assert len(inf1.sections) == len(inf2.sections)


def test_file_not_found():
    with pytest.raises(FileNotFoundError):
        Information.from_file(Path("no_such.inf"))


def test_empty_file():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "empty.inf"
        p.write_text("", encoding="utf-8")
        inf = Information.from_file(p)
        assert len(inf.sections) == 0
