#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMF 模型单元测试
"""
import xml.etree.ElementTree as ET

from comtrade_io.dmf import (ACCBranch, ACVBranch, AnalogChannel, Bus, Capacitance, ComtradeModel, Igap, Impedance,
                             Line, MutualInductance, StatusChannel, Transformer, TransformerWinding)
from comtrade_io.type import (AnalogChannelFlag, AnalogChannelType, Contact, CtDirection, DigitalChannelFlag,
                              DigitalChannelType, LineBranchNum, Phase, TranSide, TransWindLocation,
                              TvInstallSite, Unit, WindFlag)


# ========================================
# ACVBranch 测试
# ========================================
def test_acvbranch_from_xml():
    """测试 ACVBranch.from_xml"""
    xml = '''<ACVChn ua_idx="1" ub_idx="2" uc_idx="3" un_idx="4" ul_idx="5"/>'''
    element = ET.fromstring(xml)
    acv = ACVBranch.from_xml(element)

    assert acv.ua_idx == 1
    assert acv.ub_idx == 2
    assert acv.uc_idx == 3
    assert acv.un_idx == 4
    assert acv.ul_idx == 5


def test_acvbranch_from_xml_empty():
    """测试 ACVBranch.from_xml 空值情况"""
    xml = '''<ACVChn ua_idx="" ub_idx="" uc_idx=""/>'''
    element = ET.fromstring(xml)
    acv = ACVBranch.from_xml(element)

    assert acv.ua_idx == 0
    assert acv.ub_idx == 0
    assert acv.uc_idx == 0


# ========================================
# ACCBranch 测试
# ========================================
def test_accbranch_from_xml():
    """测试 ACCBranch.from_xml"""
    xml = '''<ACC_Bran bran_idx="1" ia_idx="1" ib_idx="2" ic_idx="3" in_idx="4" dir="POS"/>'''
    element = ET.fromstring(xml)
    acc = ACCBranch.from_xml(element)

    assert acc.idx == 1
    assert acc.ia_idx == 1
    assert acc.ib_idx == 2
    assert acc.ic_idx == 3
    assert acc.in_idx == 4
    assert acc.dir == CtDirection.POS


# ========================================
# Bus 测试
# ========================================
def test_bus_from_xml():
    """测试 Bus.from_xml"""
    xml = '''
    <scl:Bus idx="1" bus_name="Bus1" srcRef="ref1" VRtg="110.0" VRtgSnd="100.0"
         VRtgSnd_Pos="BUS" bus_uuid="uuid1" xmlns:scl="http://www.iec.ch/61850/2003/SCL">
        <scl:ACVChn ua_idx="1" ub_idx="2" uc_idx="3"/>
        <scl:AnaChn idx_cfg="1"/>
        <scl:AnaChn idx_cfg="2"/>
        <scl:StaChn idx_cfg="3"/>
    </scl:Bus>
    '''
    element = ET.fromstring(xml)
    ns = {'scl': 'http://www.iec.ch/61850/2003/SCL'}
    bus = Bus.from_xml(element, ns)

    assert bus.index == 1
    assert bus.name == "Bus1"
    assert bus.reference == "ref1"
    assert bus.rated_primary_voltage == 110.0
    assert bus.rated_secondary_voltage == 100.0
    assert bus.tv_install_site == TvInstallSite.BUS
    assert bus.uuid == "uuid1"
    assert bus.voltage.ua_idx == 1
    assert bus.analog_chn == [1, 2]
    assert bus.digital_chn == [3]


# ========================================
# Line 测试
# ========================================
def test_line_from_xml():
    """测试 Line.from_xml"""
    xml = '''
    <Line idx="1" line_name="Line1" bus_ID="1" srcRef="ref1" VRtg="110.0"
          ARtg="1000.0" ARtgSnd="5.0" LinLen="10.5" bran_num="B1" line_uuid="uuid1">
        <RX r1="0.1" x1="0.2" r0="0.3" x0="0.4"/>
        <CG c1="0.01" c0="0.02" g1="0.001" g0="0.002"/>
        <MR idx="1" mr0="0.5" mx0="0.6"/>
        <ACC_Bran bran_idx="1" ia_idx="1" ib_idx="2" ic_idx="3" in_idx="4" dir="POS"/>
        <AnaChn idx_cfg="1"/>
        <StaChn idx_cfg="2"/>
    </Line>
    '''
    element = ET.fromstring(xml)
    ns = {}
    line = Line.from_xml(element, ns)

    assert line.index == 1
    assert line.name == "Line1"
    assert line.bus_index == 1
    assert line.rated_primary_voltage == 110.0
    assert line.rated_primary_current == 1000.0
    assert line.line_length == 10.5
    assert line.bran_num == LineBranchNum.B1
    assert line.impedance.r1 == 0.1
    assert line.capacitance.c0 == 0.02
    assert line.mutual_inductance.idx == 1
    assert len(line.currents) == 1
    assert line.ana_chn == [1]
    assert line.sta_chn == [2]


# ========================================
# TransformerWinding 测试
# ========================================
def test_transformer_winding_from_xml():
    """测试 TransformerWinding.from_xml"""
    xml = '''
    <TransformerWinding location="HIGH" srcRef="ref1" VRtg="110.0" ARtg="1000.0"
                        bran_num="2" bus_ID="1">
        <WG wgroup="Y" angle="0"/>
        <ACVChn ua_idx="1" ub_idx="2" uc_idx="3"/>
        <ACC_Bran bran_idx="1" ia_idx="4" ib_idx="5" ic_idx="6" in_idx="7" dir="POS"/>
        <Igap zGap_idx="8" zSGap_idx="9"/>
    </TransformerWinding>
    '''
    element = ET.fromstring(xml)
    ns = {}
    analog_channels = {
        1: AnalogChannel(index=1, idx_org=1),
        2: AnalogChannel(index=2, idx_org=2),
        3: AnalogChannel(index=3, idx_org=3),
        4: AnalogChannel(index=4, idx_org=4),
        5: AnalogChannel(index=5, idx_org=5),
        6: AnalogChannel(index=6, idx_org=6),
        7: AnalogChannel(index=7, idx_org=7),
        8: AnalogChannel(index=8, idx_org=8),
        9: AnalogChannel(index=9, idx_org=9),
    }
    winding = TransformerWinding.from_xml(element, ns, analog_channels=analog_channels)

    assert winding.trans_wind_location == TransWindLocation.HIGH
    assert winding.reference == "ref1"
    assert winding.rated_voltage == 110.0
    assert winding.rated_current == 1000.0
    assert winding.bran_num == 2
    assert winding.bus_id == 1
    assert winding.wind_group.wind_flag == WindFlag.Y
    assert winding.wind_group.angle == 0
    assert winding.voltage.ua.index == 1
    assert len(winding.currents) == 1
    assert winding.igap.zgap.index == 8
    assert winding.igap.zsgap.index == 9


# ========================================
# Transformer 测试
# ========================================
def test_transformer_from_xml():
    """测试 Transformer.from_xml"""
    xml = '''
    <Transformer idx="1" trm_name="Transformer1" srcRef="ref1" pwrRtg="100.0"
                 transformer_uuid="uuid1">
        <TransformerWinding location="HIGH" srcRef="wref1" VRtg="110.0" ARtg="1000.0"
                            bran_num="2" bus_ID="1">
            <WG wgroup="Y" angle="0"/>
            <ACVChn ua_idx="1" ub_idx="2" uc_idx="3"/>
        </TransformerWinding>
        <AnaChn idx_cfg="1"/>
        <StaChn idx_cfg="2"/>
    </Transformer>
    '''
    element = ET.fromstring(xml)
    ns = {}
    transformer = Transformer.from_xml(element, ns)

    assert transformer.index == 1
    assert transformer.name == "Transformer1"
    assert transformer.capacity == 100.0
    assert len(transformer.transWinds) == 1
    assert transformer.ana_chn == [1]
    assert transformer.sta_chn == [2]


def test_analog_channel_from_xml():
    """测试 AnalogChannel.from_xml"""
    xml = '''
    <AnalogChannel idx_cfg="1" idx_org="10" type="A" flag="ACC" p_min="0.0" p_max="100.0"
                   s_min="0.0" s_max="10.0" freq="50.0" au="1.0" bu="0.0"
                   ph="A" sIUnit="V" multiplier="1.0" primary="110.0" secondary="100.0" ps="PRIMARY"/>
    '''
    element = ET.fromstring(xml)
    analog = AnalogChannel.from_xml(element)

    assert analog.index == 1
    assert analog.idx_org == 10
    assert analog.type == AnalogChannelType.A
    assert analog.flag == AnalogChannelFlag.ACC
    assert analog.p_min == 0.0
    assert analog.p_max == 100.0
    assert analog.primary == 110.0
    assert analog.secondary == 100.0
    assert analog.tran_side == TranSide.S
    assert analog.phase == Phase.PHASE_A
    assert analog.unit == Unit.V


# ========================================
# StatusChannel 测试
# ========================================
def test_status_channel_from_xml():
    """测试 StatusChannel.from_xml"""
    xml = '''
    <StatusChannel idx_cfg="1" idx_org="10" type="Breaker" flag="Status"
                   contact="NormallyOpen" srcRef="ref1"/>
    '''
    element = ET.fromstring(xml)
    status = StatusChannel.from_xml(element)

    assert status.index == 1
    assert status.idx_org == 10
    assert status.type == DigitalChannelType.BREAKER
    assert status.flag == DigitalChannelFlag.STATUS
    assert status.contact == Contact.NORMALLY_OPEN
    assert status.reference == "ref1"


# ========================================
# ComtradeModel 测试
# ========================================
def test_data_model_fault_from_xml():
    """测试 ComtradeModel.from_xml"""
    xml = '''
    <ComtradeModel xmlns:scl="http://www.iec.ch/61850/2003/SCL">
        <scl:Bus idx="1" bus_name="Bus1" srcRef="ref1" VRtg="110.0" VRtgSnd="100.0"
             VRtgSnd_Pos="BUS" bus_uuid="uuid1">
            <scl:ACVChn ua_idx="1" ub_idx="2" uc_idx="3"/>
            <scl:AnaChn idx_cfg="1"/>
            <scl:AnaChn idx_cfg="2"/>
            <scl:StaChn idx_cfg="3"/>
        </scl:Bus>
        <scl:Line idx="1" line_name="Line1" bus_ID="1" srcRef="ref1" VRtg="110.0"
              ARtg="1000.0" ARtgSnd="5.0" LinLen="10.5" bran_num="B1" line_uuid="uuid1">
            <scl:RX r1="0.1" x1="0.2" r0="0.3" x0="0.4"/>
            <scl:CG c1="0.01" c0="0.02" g1="0.001" g0="0.002"/>
            <scl:MR idx="1" mr0="0.5" mx0="0.6"/>
            <scl:ACC_Bran bran_idx="1" ia_idx="1" ib_idx="2" ic_idx="3" in_idx="4" dir="POS"/>
            <scl:AnaChn idx_cfg="1"/>
            <scl:StaChn idx_cfg="2"/>
        </scl:Line>
        <scl:Transformer idx="1" trm_name="Transformer1" srcRef="ref1" pwrRtg="100.0"
                     transformer_uuid="uuid1">
            <scl:TransformerWinding location="HIGH" srcRef="wref1" VRtg="110.0" ARtg="1000.0"
                                bran_num="2" bus_ID="1">
                <scl:WG wgroup="Y" angle="0"/>
                <scl:ACVChn ua_idx="1" ub_idx="2" uc_idx="3"/>
                <scl:ACC_Bran bran_idx="1" ia_idx="4" ib_idx="5" ic_idx="6" in_idx="7" dir="POS"/>
            </scl:TransformerWinding>
            <scl:AnaChn idx_cfg="1"/>
            <scl:StaChn idx_cfg="2"/>
        </scl:Transformer>
        <scl:AnalogChannel idx_cfg="1" idx_org="10" type="A" flag="ACC" p_min="0.0" p_max="100.0"
                       s_min="0.0" s_max="10.0" freq="50.0" au="1.0" bu="0.0"
                       ph="A" sIUnit="V" multiplier="1.0" primary="110.0" secondary="100.0" ps="PRIMARY"/>
        <scl:StatusChannel idx_cfg="1" idx_org="10" type="Breaker" flag="Status"
                       contact="NormallyOpen" srcRef="ref1"/>
    </ComtradeModel>
    '''
    element = ET.fromstring(xml)
    ns = {'scl': 'http://www.iec.ch/61850/2003/SCL'}
    dmf = ComtradeModel.from_xml(element, ns)

    assert len(dmf.buses) == 1
    assert len(dmf.lines) == 1
    assert len(dmf.transformers) == 1
    assert len(dmf.analog_channels) == 1
    assert len(dmf.status_channels) == 1
    assert dmf.buses[0].name == "Bus1"
    assert dmf.lines[0].name == "Line1"
    assert dmf.transformers[0].name == "Transformer1"


def test_data_model_fault_from_xml_no_namespace():
    """测试 ComtradeModel.from_xml 无命名空间情况"""
    xml = '''
    <ComtradeModel>
        <Bus idx="1" bus_name="Bus1" srcRef="ref1" VRtg="110.0" VRtgSnd="100.0"
             VRtgSnd_Pos="BUS" bus_uuid="uuid1">
            <ACVChn ua_idx="1" ub_idx="2" uc_idx="3"/>
            <AnaChn idx_cfg="1"/>
            <AnaChn idx_cfg="2"/>
            <StaChn idx_cfg="3"/>
        </Bus>
    </ComtradeModel>
    '''
    element = ET.fromstring(xml)
    dmf = ComtradeModel.from_xml(element, {})

    assert len(dmf.buses) == 1
    assert dmf.buses[0].name == "Bus1"


# ========================================
# 辅助类测试
# ========================================
def test_rx():
    """测试 RX 类"""
    rx = Impedance(r1=0.1, x1=0.2, r0=0.3, x0=0.4)
    assert rx.r1 == 0.1
    assert rx.x1 == 0.2
    assert rx.r0 == 0.3
    assert rx.x0 == 0.4


def test_cg():
    """测试 CG 类"""
    cg = Capacitance(c1=0.01, c0=0.02, g1=0.001, g0=0.002)
    assert cg.c1 == 0.01
    assert cg.c0 == 0.02


def test_mr():
    """测试 MR 类"""
    mr = MutualInductance(idx=1, mr0=0.5, mx0=0.6)
    assert mr.idx == 1
    assert mr.mr0 == 0.5


def test_igap():
    """测试 Igap 类"""
    zgap_ch = AnalogChannel(index=1, idx_org=1)
    zsgap_ch = AnalogChannel(index=2, idx_org=2)
    igap = Igap(zgap=zgap_ch, zsgap=zsgap_ch)
    assert igap.zgap.index == 1
    assert igap.zsgap.index == 2


def test_igap_from_xml():
    """测试 Igap.from_xml"""
    xml = '''<Igap zGap_idx="8" zSGap_idx="9"/>'''
    element = ET.fromstring(xml)
    analog_channels = {
        8: AnalogChannel(index=8, idx_org=1),
        9: AnalogChannel(index=9, idx_org=2)
    }
    igap = Igap.from_xml(element, {}, analog_channels=analog_channels)

    assert igap.zgap.index == 8
    assert igap.zsgap.index == 9


def test_igap_from_xml_without_analog_channels():
    """测试 Igap.from_xml 不传入 analog_channels 的情况"""
    xml = '''<Igap zGap_idx="8" zSGap_idx="9"/>'''
    element = ET.fromstring(xml)
    igap = Igap.from_xml(element, {})

    assert igap.zgap is None
    assert igap.zsgap is None
