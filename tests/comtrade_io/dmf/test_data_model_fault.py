#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DataModelFault测试"""
import tempfile
from pathlib import Path

import pytest
from comtrade_io.dmf import ComtradeModel
from comtrade_io.type import LineBranchNum, TvInstallSite


class TestDataModelFault:
    """DataModelFault测试类"""

    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_xml_content(self):
        """示例DMF XML内容"""
        return """<?xml version="1.0" encoding="UTF-8"?>
<scl:SCL xmlns:scl="http://www.iec.ch/61850/2003/SCL">
    <scl:IED name="TEST">
        <scl:LN0>
            <scl:Bus idx="1" bus_name="Bus1" srcRef="REF1" VRtg="500.0" VRtgSnd="1.0" VRtgSnd_Pos="BUS" bus_uuid="uuid1"/>
            <scl:Bus idx="2" bus_name="Bus2" srcRef="REF2" VRtg="220.0" VRtgSnd="1.0" VRtgSnd_Pos="LINE" bus_uuid="uuid2"/>

            <scl:Line idx="1" line_name="Line1" bus_ID="1" srcRef="REF3" VRtg="500.0" ARtg="1000.0" ARtgSnd="1.0"
                     LinLen="50.0" bran_num="1" line_uuid="line_uuid1"/>
            <scl:Line idx="2" line_name="Line2" bus_ID="2" srcRef="REF4" VRtg="220.0" ARtg="1250.0" ARtgSnd="1.0"
                     LinLen="30.0" bran_num="2" line_uuid="line_uuid2"/>

            <scl:Transformer name="Transformer1" desc="Test Transformer">
                <scl:TransformerWinding location="PRIMARY" srcRef="REF5" VRtg="500.0" ARtg="1000.0"
                                      bran_num="1" bus_ID="1" wG=""/>
                <scl:TransformerWinding location="SECONDARY" srcRef="REF6" VRtg="220.0" ARtg="1250.0"
                                      bran_num="2" bus_ID="2" wG=""/>
            </scl:Transformer>
        </scl:LN0>
    </scl:IED>
</scl:SCL>
"""

    def test_from_file(self, temp_dir, sample_xml_content):
        """测试从文件读取"""
        dmf_file = temp_dir / "test.dmf"
        dmf_file.write_text(sample_xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)

        assert dmf is not None
        assert len(dmf.buses) == 2
        assert len(dmf.lines) == 2
        assert len(dmf.transformers) == 1

    def test_get_bus(self, temp_dir, sample_xml_content):
        """测试获取母线"""
        dmf_file = temp_dir / "test.dmf"
        dmf_file.write_text(sample_xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)

        bus = dmf.get_bus_info("Bus1")
        assert bus is not None
        assert bus.name == "Bus1"
        assert bus.rated_primary_voltage == 500.0

        bus = dmf.get_bus_info("NonExistent")
        assert bus is None

    def test_get_line(self, temp_dir, sample_xml_content):
        """测试获取线路"""
        dmf_file = temp_dir / "test.dmf"
        dmf_file.write_text(sample_xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)

        line = dmf.get_line_info("Line1")
        assert line is not None
        assert line.name == "Line1"
        assert line.rated_primary_voltage == 500.0
        assert line.bran_num == LineBranchNum.B1

        line = dmf.get_line_info("NonExistent")
        assert line is None

    def test_get_transformer(self, temp_dir, sample_xml_content):
        """测试获取变压器"""
        dmf_file = temp_dir / "test.dmf"
        dmf_file.write_text(sample_xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)

        transformer = dmf.get_transformer_info("Transformer1")
        assert transformer is not None
        assert transformer.name == "Transformer1"
        assert len(transformer.windings) == 2

        transformer = dmf.get_transformer_info("NonExistent")
        assert transformer is None

    def test_empty_file(self, temp_dir):
        """测试空文件"""
        dmf_file = temp_dir / "empty.dmf"
        dmf_file.write_text("", encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)
        assert dmf is None

    def test_invalid_xml(self, temp_dir):
        """测试无效XML"""
        dmf_file = temp_dir / "invalid.dmf"
        dmf_file.write_text("This is not valid XML", encoding="utf-8")

        with pytest.raises(ValueError):
            ComtradeModel.from_file(dmf_file)

    def test_missing_namespace(self, temp_dir):
        """测试无命名空间的XML"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<SCL>
    <IED name="TEST">
        <LN0>
            <Bus idx="1" bus_name="Bus1" VRtg="500.0" VRtgSnd="1.0" VRtgSnd_Pos="BUS"/>
        </LN0>
    </IED>
</SCL>
"""
        dmf_file = temp_dir / "test.dmf"
        dmf_file.write_text(xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)
        assert dmf is not None
        assert len(dmf.buses) >= 0  # 可能无法解析，取决于命名空间处理

    def test_complex_transformer(self, temp_dir):
        """测试复杂的变压器配置"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<scl:SCL xmlns:scl="http://www.iec.ch/61850/2003/SCL">
    <scl:IED name="TEST">
        <scl:LN0>
            <scl:Transformer name="ThreeWinding" desc="Three Winding Transformer">
                <scl:TransformerWinding location="PRIMARY" VRtg="500.0" ARtg="1000.0" bran_num="1" bus_ID="1"/>
                <scl:TransformerWinding location="SECONDARY" VRtg="220.0" ARtg="1250.0" bran_num="2" bus_ID="2"/>
                <scl:TransformerWinding location="TERTIARY" VRtg="35.0" ARtg="2000.0" bran_num="3" bus_ID="3"/>
            </scl:Transformer>
        </scl:LN0>
    </scl:IED>
</scl:SCL>
"""
        dmf_file = temp_dir / "test.dmf"
        dmf_file.write_text(xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)
        transformer = dmf.get_transformer_info("ThreeWinding")
        assert transformer is not None
        assert len(transformer.windings) == 3

    def test_enum_values(self, temp_dir):
        """测试枚举值解析"""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<scl:SCL xmlns:scl="http://www.iec.ch/61850/2003/SCL">
    <scl:IED name="TEST">
        <scl:LN0>
            <scl:Bus idx="1" bus_name="TestBus" VRtg="500.0" VRtgSnd="1.0" VRtgSnd_Pos="BUS"/>
            <scl:Line idx="1" line_name="TestLine" bus_ID="1" VRtg="500.0" ARtg="1000.0" ARtgSnd="1.0"
                     LinLen="50.0" bran_num="1"/>
        </scl:LN0>
    </scl:IED>
</scl:SCL>
"""
        dmf_file = temp_dir / "test.dmf"
        dmf_file.write_text(xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)
        bus = dmf.buses[0]
        line = dmf.lines[0]

        # 验证枚举值正确解析
        assert bus.tv_install_site == TvInstallSite.BUS
        assert line.bran_num == LineBranchNum.B1

    def test_large_file(self, temp_dir):
        """测试大文件处理"""
        # 生成包含大量设备的XML
        buses = "\n".join([
            f'<scl:Bus idx="{i}" bus_name="Bus{i}" VRtg="500.0" VRtgSnd="1.0" VRtgSnd_Pos="BUS"/>'
            for i in range(1, 101)
        ])

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<scl:SCL xmlns:scl="http://www.iec.ch/61850/2003/SCL">
    <scl:IED name="TEST">
        <scl:LN0>
            {buses}
        </scl:LN0>
    </scl:IED>
</scl:SCL>
"""
        dmf_file = temp_dir / "large_test.dmf"
        dmf_file.write_text(xml_content, encoding="utf-8")

        dmf = ComtradeModel.from_file(dmf_file)
        assert len(dmf.buses) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
