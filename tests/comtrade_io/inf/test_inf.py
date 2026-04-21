#!/usr/bin/env python
# -*- coding: utf-8 -*-
import tempfile
from pathlib import Path

from comtrade_io.inf import Information


def test_parse_section_header():
    """测试节头解析函数"""
    from comtrade_io.inf.information import parse_section_header

    # 测试正常格式
    result = parse_section_header("[Public Analog_Channel_#1]")
    assert result is not None
    assert result["area"] == "Public"
    assert result["type"] == "Analog_Channel"
    assert result["index"] == 1

    # 测试ZYHD格式
    result = parse_section_header("[ZYHD Bus_#2]")
    assert result is not None
    assert result["area"] == "ZYHD"
    assert result["type"] == "Bus"
    assert result["index"] == 2

    # 测试无索引格式
    result = parse_section_header("[Public Record_Information]")
    assert result is not None
    assert result["area"] == "Public"
    assert result["type"] == "Record_Information"
    assert result["index"] == 0

    # 测试无效格式
    assert parse_section_header("Invalid Format") is None
    assert parse_section_header("[MissingSpace]") is None


def test_parse_basic_sections():
    """测试基础节解析"""
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
        model = Information.from_file(p)
        assert model is not None


def test_parse_analog_channels():
    """测试模拟通道解析"""
    from comtrade_io.type import Phase, Unit

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
[Public Analog_Channel_#1]
Channel_ID=Ia
Phase_ID=A
Monitored_Component=TCTR$MX$Amp$
Channel_Units=A
Channel_Multiplier=0.01
Channel_Offset=0.0
Channel_Skew=0.0
Range_Minimum_Limit_Value=-32767
Range_Maximum_Limit_Value=32767
Channel_Ratio_Primary=1000
Channel_Ratio_Secondary=1
Data_Primary_Secondary=S

[Public Analog_Channel_#2]
Channel_ID=Ib
Phase_ID=B
Channel_Units=A
            """.strip(),
            encoding="utf-8"
        )
        model = Information.from_file(p)
        assert model is not None
        assert len(model.analogs) == 2

        # 检查第一个通道
        ana1 = model.analogs[1]
        assert ana1.index == 1
        assert ana1.name == "Ia"
        assert ana1.phase == Phase.PHASE_A
        assert ana1.reference == "TCTR$MX$Amp$"
        assert ana1.unit == Unit.A
        assert ana1.multiplier == 0.01
        assert ana1.primary == 1000.0
        assert ana1.secondary == 1.0

        # 检查第二个通道
        ana2 = model.analogs[2]
        assert ana2.index == 2
        assert ana2.name == "Ib"
        assert ana2.phase == Phase.PHASE_B


def test_parse_status_channels():
    """测试状态通道解析"""
    from comtrade_io.type import Phase, Contact

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
[Public Status_Channel_#1]
Channel_ID=Breaker1
Phase_ID=A
Monitored_Component=XCBR$ST$Pos$
Normal_State=0

[Public Status_Channel_#2]
Channel_ID=Breaker2
Phase_ID=B
Normal_State=1
            """.strip(),
                encoding="utf-8"
        )
        model = Information.from_file(p)
        assert model is not None
        assert len(model.statuses) == 2

        sta1 = model.statuses[1]
        assert sta1.index == 1
        assert sta1.name == "Breaker1"
        assert sta1.phase == Phase.PHASE_A
        assert sta1.reference == "XCBR$ST$Pos$"
        assert sta1.contact == Contact.NormallyOpen

        sta2 = model.statuses[2]
        assert sta2.index == 2
        assert sta2.contact == Contact.NormallyClosed


def test_parse_equipment_sections():
    """测试设备节解析"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
                """
    [Public Analog_Channel_#1]
    Channel_ID=Ua
    Phase_ID=A
    Channel_Units=kV
    
    [Public Analog_Channel_#2]
    Channel_ID=Ub
    Phase_ID=B
    Channel_Units=kV
    
    [Public Analog_Channel_#3]
    Channel_ID=Uc
    Phase_ID=C
    Channel_Units=kV
    
    [Public Analog_Channel_#4]
    Channel_ID=Ia
    Phase_ID=A
    Channel_Units=A
    
    [Public Analog_Channel_#5]
    Channel_ID=Ib
    Phase_ID=B
    Channel_Units=A
    
    [Public Analog_Channel_#6]
    Channel_ID=Ic
    Phase_ID=C
    Channel_Units=A
    
    [Public Status_Channel_#1]
    Channel_ID=Brk1
    Normal_State=0
    
    [ZYHD Bus_#1]
    DEV_ID=,Bus1
    SYS_ID=bus-001
    TV_CHNS=1,2,3
    STATUS_CHNS=1
    TV_RATIO=220kV/100V
    TV_POS=BUS
    
    [ZYHD Line_#1]
    DEV_ID=,Line1
    SYS_ID=line-001
    TA_CHNS=4,5,6
    STATUS_CHNS=1
    LENGTH=10.5(km)
    RX=0.01,0.1,0.03,0.3
    CG=0.01,0.001,0.02,0.002
    MRX=0.005,0.05
    
    [ZYHD Transformer_#1]
    DEV_ID=,Tr1
    SYS_ID=tr-001
    CAPACITY=100
    WINDING_NUM=3
    H_PARAM=Y, 220, 1
    H_TV_CHNS=1,2,3
    TA_Id_#5=4,5,6
                """.strip(),
            encoding="utf-8"
        )
        model = Information.from_file(p)
        assert model is not None

        # 检查母线
        assert len(model.buses) == 1
        bus = model.buses[0]
        assert bus.index == 1
        assert bus.name == "Bus1"
        assert bus.uuid == "bus-001"
        assert len(bus.acvs) == 3
        assert bus.rated_primary_voltage == 220.0

        # 检查线路
        assert len(model.lines) == 1
        line = model.lines[0]
        assert line.index == 1
        assert line.name == "Line1"
        assert line.line_length == 10.5
        assert line.impedance.r1 == 0.01
        assert line.impedance.x1 == 0.1
        assert line.capacitance.c1 == 0.01

        # 检查变压器
        assert len(model.transformers) == 1
        tr = model.transformers[0]
        assert tr.index == 1
        assert tr.name == "Tr1"
        assert tr.capacity == 100.0


def test_parse_with_name_field():
    """测试使用Name字段（无逗号）的情况"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
            """
[ZYHD Bus_#1]
Name=BusDirect
            """.strip(),
                encoding="utf-8"
        )
        model = Information.from_file(p)
        assert model is not None
        assert len(model.buses) == 1
        assert model.buses[0].name == "BusDirect"


def test_parse_empty_name():
    """测试设备名称为空时的默认值"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "sample.inf"
        p.write_text(
                """
    [ZYHD Bus_#5]
    DEV_ID=
                """.strip(),
            encoding="utf-8"
        )
        model = Information.from_file(p)
        assert model is not None
        assert len(model.buses) == 1
        assert model.buses[0].name == "Equipment_5"


def test_file_not_found():
    """测试文件不存在的情况"""
    # 当前实现返回None而不是抛出异常
    model = Information.from_file(Path("no_such_file.inf"))
    assert model is None


def test_empty_content():
    """测试空内容解析（直接测试 split_sections）"""
    from comtrade_io.inf.information import Information

    inf = Information()
    inf.split_sections("")
    assert len(inf.analog_channels) == 0
    assert len(inf.status_channels) == 0
    assert len(inf.buses) == 0
    assert len(inf.lines) == 0
    assert len(inf.transformers) == 0


def test_comtrade_model_fields():
    """测试 ComtradeModel 字段类型正确"""
    from comtrade_io.equipment import EquipmentGroup

    model = EquipmentGroup()
    assert isinstance(model.analogs, dict)
    assert isinstance(model.statuses, dict)
    assert isinstance(model.buses, list)
    assert isinstance(model.lines, list)
    assert isinstance(model.transformers, list)


def test_from_str():
    """测试 from_str 方法直接解析字符串"""
    from comtrade_io.type import Phase

    content = """
[Public Analog_Channel_#1]
Channel_ID=Ia
Phase_ID=A
Channel_Units=A

[Public Analog_Channel_#2]
Channel_ID=Ib
Phase_ID=B
Channel_Units=A

[ZYHD Bus_#1]
DEV_ID=,Bus1
    """.strip()

    model = Information.from_str(content)
    assert model is not None
    assert len(model.analogs) == 2
    assert model.analogs[1].name == "Ia"
    assert model.analogs[1].phase == Phase.PHASE_A
    assert model.analogs[2].name == "Ib"
    assert len(model.buses) == 1
    assert model.buses[0].name == "Bus1"


def test_from_str_empty():
    """测试 from_str 解析空字符串"""
    model = Information.from_str("")
    assert len(model.analogs) == 0
    assert len(model.statuses) == 0
    assert len(model.buses) == 0


def test_kv_pairs():
    """测试键值对解析"""
    from comtrade_io.inf.information import _kv_pairs

    lines = [
        "[Section]",
        "Key1=Value1",
        "Key2 = Value2 ",
        "  Key3=Value3  ",
        "InvalidLine",
        "Key4=Value4"
    ]
    result = _kv_pairs(lines)
    assert result["Key1"] == "Value1"
    assert result["Key2"] == "Value2"
    assert result["Key3"] == "Value3"
    assert result["Key4"] == "Value4"
    assert "InvalidLine" not in result


def test_encoding_handling():
    """测试编码处理"""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "gbk.inf"
        p.write_text(
                """
    [Public Record_Information]
    Source=测试源
    Location=测试位置
                """.strip(),
                encoding="gbk"
        )
        model = Information.from_file(p)
        assert model is not None


def test_read_real_binary_inf_file():
    """测试读取实际的binary_inf.inf文件"""
    # 获取测试数据文件的路径
    test_dir = Path(__file__).parent.parent.parent / "data"
    inf_file = test_dir / "binary_inf.inf"

    # 确保文件存在
    assert inf_file.exists(), f"测试文件不存在: {inf_file}"

    # 读取并解析INF文件
    model = Information.from_file(inf_file)

    # 验证解析成功
    assert model is not None, "INF文件解析失败"

    # 验证基本属性 - 根据binary_inf.inf文件内容
    # 文件中有Total_Channel_Count=356, Analog_Channel_Count=155, Status_Channel_Count=201
    # 但EquipmentGroup只包含analogs和statuses字典，我们可以验证这些字典的长度
    # 注意：EquipmentGroup中的analogs和statuses是字典，键从1开始
    assert len(model.analogs) == 155, f"模拟通道数量应为155，实际为{len(model.analogs)}"
    assert len(model.statuses) == 201, f"状态通道数量应为201，实际为{len(model.statuses)}"

    # 验证description中的站点名称（从文件第12行：Station_Name=220kV���վ����）
    # 注意：中文字符可能被正确解析，我们至少验证非空
    assert model.description is not None
    assert model.description.station_name != ""

    # 验证录波设备ID（Recording_Device_ID=ZH3D-1）
    assert model.description.rec_dev_name == "ZH3D-1"

    # 验证版本（Revision_Year=1999）
    from comtrade_io.type import Version
    assert model.description.version == Version.V1999

    # 验证文件类型为BINARY（File_Type=BINARY）
    # 这个信息可能不在EquipmentGroup中，但我们至少可以验证解析没有出错
    # 同时验证其他设备部分（母线、线路、变压器）可能为空
    # 根据文件内容，可能没有这些部分，我们只验证它们存在且为列表
    assert isinstance(model.buses, list)
    assert isinstance(model.lines, list)
    assert isinstance(model.transformers, list)

    print(f"成功解析INF文件: {inf_file}")
    print(f"模拟通道数: {len(model.analogs)}")
    print(f"状态通道数: {len(model.statuses)}")
    print(f"站点名称: {model.description.station_name}")
    print(f"录波设备: {model.description.rec_dev_name}")
    print(f"版本: {model.description.version}")
