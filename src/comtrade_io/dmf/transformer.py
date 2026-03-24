#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
变压器模型模块

定义变压器相关类，包括绕组类、互感类、变压器类等。
变压器是电力系统中的关键设备，用于改变电压等级和传输功率。
"""
from typing import List, Optional
from xml.etree.ElementTree import Element

from comtrade_io.dmf.analog_channel import AnalogChannel
from comtrade_io.dmf.branch import ACCBranch, ACVBranch
from comtrade_io.dmf.dmf_base_model import DmfBaseModel
from comtrade_io.type import TransWindLocation, WindFlag
from comtrade_io.utils import parse_float, parse_int
from pydantic import BaseModel, Field


class WindGroup(BaseModel):
    """
    绕组标识类
    
    表示变压器的绕组标识信息，用于标识不同的绕组及其相位关系。
    
    属性:
        wgroup: 绕组标识符，如Y（星形）、D（三角形）等
        angle: 绕组角度，表示星形连接绕组的相角偏移
    """
    wgroup: WindFlag = Field(default=WindFlag.Y, description="绕组标识符")
    angle: int = Field(default=0, description="绕组角度")


class Igap(BaseModel):
    """
    中性点电流类
    
    表示变压器中性点的接地电流通道信息，用于记录中性点电流测量。
    
    实例化时可以传入通道索引和analog_channels字典，会自动解析为AnalogChannel对象。
    也可以直接传入AnalogChannel对象。

    属性:
        zgap_idx: 中性点直接接地电流的通道
        zsgap_idx: 中性点经间隙接地电流的通道
    """
    zgap: Optional[AnalogChannel] = Field(default=None, description="中性点直接接地电流的通道")
    zsgap: Optional[AnalogChannel] = Field(default=None, description="中性点经间隙接地电流的通道")

    def __str__(self):
        """
        返回中性点电流的XML字符串表示形式
        
        返回:
            格式化的XML字符串，表示中性点电流通道信息
        """
        zgap_idx = self.zgap.index if self.zgap else 0
        zsgap_idx = self.zsgap.index if self.zsgap else 0
        xml = f"<scl:Igap zGap_idx={zgap_idx} zSGap_idx={zsgap_idx} />"
        return xml

    @classmethod
    def from_xml(cls, element: Element, ns: dict = None, analog_channels: dict = None) -> "Igap":
        """
        从XML元素中解析中性点电流

        参数:
            element: XML元素
            ns: 命名空间映射（可选）
            analog_channels: 模拟通道字典（可选），用于解析通道对象

        返回:
            Igap: 中性点电流实例
        """
        zgap_idx_val = parse_int(element.get("zGap_idx", 0))
        zsgap_idx_val = parse_int(element.get("zSGap_idx", 0))

        if analog_channels is None:
            return cls()
        kwargs = {}
        if zgap_idx_val:
            kwargs["zgap_idx"] = analog_channels.get(zgap_idx_val, None)
        if zsgap_idx_val:
            kwargs["zsgap_idx"] = analog_channels.get(zsgap_idx_val, None)

        return cls(**kwargs)


class TransformerWinding(BaseModel):
    """
    变压器绕组类
    
    表示变压器的单个绕组，包含绕组的电气参数和关联的电压电流通道。
    一个变压器可以有多个绕组（通常是高压绕组和低压绕组）。
    
    属性:
        bus_id: 母线索引号，表示该绕组连接的母线
        location: 绕组位置，标识绕组是高压侧还是低压侧
        reference: IEC61850参引，用于关联到IEC61850数据模型
        v_rtg: 额定电压，单位通常为kV
        a_rtg: 一次额定电流，单位通常为A
        bran_num: 分路数，表示绕组的分支数量
        wg: 绕组标识符，包含绕组类型和角度信息
        voltage: 交流电压通道，包含该绕组的电压通道索引
        currents: 交流电流通道列表，包含该绕组的电流分支信息
        igap: 中性点电流信息，包含接地电流的通道号
    """
    bus_id: int = Field(default=0, description="母线索引号")
    trans_wind_location: TransWindLocation = Field(default=TransWindLocation.HIGH, description="绕组位置")
    reference: Optional[str] = Field(default="", description="IEC61850参引")
    rated_voltage: float = Field(default=0.0, description="额定电压")
    rated_current: float = Field(default=0.0, description="一次额定电流")
    bran_num: int = Field(default=0, description="分路数")
    wind_group: WindGroup = Field(default_factory=WindGroup, description="绕组标识符")
    voltage: ACVBranch = Field(default_factory=ACVBranch, description="交流电压通道")
    currents: List[ACCBranch] = Field(default_factory=list, description="交流电流通道")
    igap: Igap = Field(default_factory=Igap, description="中性点电流通道号")

    def __str__(self):
        """
        返回变压器绕组的XML字符串表示形式
        
        返回:
            格式化的XML字符串，包含绕组及其所有子元素的完整表示
        """
        attrs = [
            f'location={self.trans_wind_location.value}"',
            f'srcRef={self.reference}"',
            f'VRtg={self.rated_voltage}"',
            f'ARtg={self.rated_current}"',
            f'bran_num={self.bran_num}"',
            f'bus_ID={self.bus_id}"',
            f'wG=""'
        ]
        attrs = [attr for attr in attrs if attr is not None]
        xml = f"<scl:TransformerWinding {' '.join(attrs)}>"
        xml += "\n\t\t\t" + str(self.voltage)
        for acc_bran in self.currents:
            xml += "\n\t\t\t" + str(acc_bran)
        xml += "\n\t\t\t" + str(self.igap)
        xml += "\n\t\t</scl:TransformerWinding>"
        return xml

    @classmethod
    def from_xml(cls, element: Element, ns: dict, analog_channels: dict = None) -> 'TransformerWinding':
        """
        从XML元素中解析变压器绕组

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典（可选），用于解析ACVBranch中的通道对象
            
        返回:
            TransformerWinding: 变压器绕组实例
        """

        location = TransWindLocation.from_value(element.get('location', ""),
                                                default=TransWindLocation.HIGH)
        src_ref = element.get('srcRef', "")
        v_rtg = parse_float(element.get('VRtg', 0.0))
        a_rtg = parse_float(element.get('ARtg', 0.0))
        bran_num = parse_int(element.get('bran_num', 0))

        # 查找 WG 元素（支持带/不带命名空间）
        wg_elem = element.find('scl:WG', ns) if 'scl' in ns else element.find('WG')
        wg = WindGroup(
            angle=parse_int(wg_elem.get('angle', 0)) if wg_elem else 0,
            wgroup=WindFlag.from_value(wg_elem.get('wgroup', "") if wg_elem else "", default=WindFlag.Y)
        )
        bus_id = parse_int(element.get('bus_ID', 0))
        tfw = cls(trans_wind_location=location, reference=src_ref, rated_voltage=v_rtg, rated_current=a_rtg,
                  bran_num=bran_num, wind_group=wg, bus_id=bus_id)

        # 查找 ACVChn 元素（支持带/不带命名空间）
        acv_chn_elem = element.find('scl:ACVChn', ns) if 'scl' in ns else element.find('ACVChn')
        if acv_chn_elem is not None:
            tfw.voltage = ACVBranch.from_xml(acv_chn_elem, ns, analog_channels=analog_channels)

        # 查找 ACC_Bran 元素（支持带/不带命名空间）
        if 'scl' in ns:
            acc_elems = element.findall('scl:ACC_Bran', ns)
        else:
            acc_elems = element.findall('ACC_Bran')
        tfw.currents = [
            ACCBranch.from_xml(chn, ns, analog_channels=analog_channels)
            for chn in acc_elems
        ]

        # 查找 Igap 元素（支持带/不带命名空间）
        igap_elem = element.find('scl:Igap', ns) if 'scl' in ns else element.find('Igap')
        if igap_elem is not None:
            zgap_idx_val = parse_int(igap_elem.get('zGap_idx', 0))
            zsgap_idx_val = parse_int(igap_elem.get('zSGap_idx', 0))
            kwargs = {}
            if zgap_idx_val and analog_channels:
                kwargs["zgap_idx"] = analog_channels.get(zgap_idx_val, None)
            if zsgap_idx_val and analog_channels:
                kwargs["zsgap_idx"] = analog_channels.get(zsgap_idx_val, None)
            tfw.igap = Igap(**kwargs)

        return tfw


class Transformer(DmfBaseModel):
    """
    变压器类
    
    表示电力系统中的变压器设备，包含额定功率和多个绕组。
    变压器是连接不同电压等级电网的关键设备。
    
    属性:
        pwr_rtg: 变压器额定功率，单位通常为MVA
        transWinds: 变压器绕组列表，包含该变压器的所有绕组
        transformer_uuid: 变压器唯一标识符
        anas: 模拟通道列表，继承自基类
        stas: 开关量通道列表，继承自基类
    """
    pwr_rtg: float = Field(default=0.0, description="变压器额定功率")
    transWinds: List[TransformerWinding] = Field(default_factory=list, description="变压器绕组")
    transformer_uuid: str = Field(default="", description="变压器标识")

    def __str__(self):
        """
        返回变压器的XML字符串表示形式
        
        返回:
            格式化的XML字符串，包含变压器及其所有绕组的完整表示
        """
        attrs = [
            f'idx="{self.index}"',
            f'trm_name="{self.name}"',
            f'srcRef="{self.reference}"',
            f'pwrRtg="{self.pwr_rtg}"',
            f'transformer_uuid="{self.uuid}"'
        ]
        attrs = [attr for attr in attrs if attr is not None]
        xml = f"\t<scl:Transformer {' '.join(attrs)} />"

        for trans_wind in self.transWinds:
            xml += "\n\t\t" + str(trans_wind)
        xml += self.get_ana_chn_xml()
        xml += self.get_sta_chn_xml()
        xml += "\n\t</scl:Transformer>"
        return xml

    @classmethod
    def from_xml(cls, element: Element, ns: dict, analog_channels: dict = None, status_channels: dict = None) -> 'Transformer':
        """
        从XML元素中解析变压器模型

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典（可选），用于解析ACVBranch中的通道对象
            status_channels: 开关量通道字典（可选），用于解析开关量通道对象
            
        返回:
            Transformer: 变压器实例
        """
        idx = parse_int(element.get('idx', 1))
        tran_name = element.get('trm_name', "")
        src_ref = element.get('srcRef', "")
        pwr_rtg = parse_float(element.get('pwrRtg', 0.0))
        uuid = element.get('transformer_uuid', "")

        tran = cls(
            index=idx,
            name=tran_name,
            reference=src_ref,
            pwr_rtg=pwr_rtg,
            uuid=uuid
        )

        # 解析变压器绕组（支持带/不带命名空间）
        if 'scl' in ns:
            tran.transWinds = [
                TransformerWinding.from_xml(tw, ns, analog_channels=analog_channels)
                for tw in element.findall('scl:TransformerWinding', ns)
            ]
            tran.anas = cls.parse_ans_from_xml(element, ns, analog_channels=analog_channels, use_scl_prefix=True)
            tran.stas = cls.parse_sts_from_xml(element, ns, status_channels=status_channels, use_scl_prefix=True)
        else:
            tran.transWinds = [
                TransformerWinding.from_xml(tw, ns, analog_channels=analog_channels)
                for tw in element.findall('TransformerWinding')
            ]
            tran.anas = cls.parse_ans_from_xml(element, ns, analog_channels=analog_channels, use_scl_prefix=False)
            tran.stas = cls.parse_sts_from_xml(element, ns, status_channels=status_channels, use_scl_prefix=False)

        return tran
