#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
母线模型模块

定义母线类，用于表示电力系统中的母线模型。
母线是电力系统中的重要节点，用于汇集和分配电能。
"""
from xml.etree.ElementTree import Element

from pydantic import Field

from comtrade_io.dmf.branch import ACVBranch
from comtrade_io.dmf.dmf_base_model import DmfBaseModelModel
from comtrade_io.type import TvInstallSite
from comtrade_io.utils import parse_float, parse_int


class Bus(DmfBaseModelModel):
    """
    母线类
    
    表示电力系统中的母线模型，是电力系统网络中的关键节点。
    母线用于汇集和分配电能，连接线路、变压器等设备。
    
    属性:
        v_rtg: 一次额定电压，单位通常为kV
        v_rtg_snd: 二次额定电压（用于保护装置的电压输入），单位通常为V
        v_rtg_snd_pos: TV安装位置，标识电压互感器的安装位置
        voltage: 电压通道，包含该母线的电压通道索引信息
        anas: 模拟通道列表，继承自基类
        stas: 开关量通道列表，继承自基类
    """
    v_rtg: float = Field(default=0.0, description="一次额定电压")
    v_rtg_snd: float = Field(default=100.0, description="二次额定电压")
    v_rtg_snd_pos: TvInstallSite = Field(default=TvInstallSite.BUS, description="TV安装位置")
    voltage: ACVBranch = Field(default=ACVBranch(), description="电压通道")

    def __str__(self):
        """
        返回母线的XML字符串表示形式
        
        返回:
            格式化的XML字符串，包含母线及其所有子元素的完整表示
        """
        attrs = [
            f'idx"={self.index}"',
            f'bus_name="{self.name}"',
            f'srcRef="{self.reference}"',
            f'VRtg="{self.v_rtg}"',
            f'VRtgSnd="{self.v_rtg_snd}"',
            f'VRtgSnd_Pos="{self.v_rtg_snd_pos}"',
            f'bus_uuid="{self.uuid}"'
        ]
        attrs = [attr for attr in attrs if attr is not None]
        xml = f"\t<scl:Bus {' '.join(attrs)}/>"
        xml += "\n\t\t" + str(self.voltage)
        xml += self.get_ana_chn_xml()
        xml += self.get_sta_chn_xml()
        xml += "\n\t</scl:Bus>"
        return xml

    def info(self):
        parts = [
            f'【母线信息】',
            f'母线名称：{self.name},内部编号索引：{self.index}',
            f'一次额定电压：{self.v_rtg}kV,二次额定电压：{self.v_rtg_snd}V',
            f'TV安装位置：{self.v_rtg_snd_pos.description}',
            f'【电压通道情况】'
        ]
        for vp in (self.voltage.ua, self.voltage.ub, self.voltage.uc, self.voltage.ul, self.voltage.un):
            if not vp:
                continue
            chn = f'通道索引号：{vp.index}，通道名称：{vp.name},{vp.phase.value}相{vp.type.description}{vp.flag.description}'
            parts.append(chn)
        return "\n".join(parts)

    @classmethod
    def from_xml(cls, element: Element, ns: dict, analog_channels: dict = None, status_channels: dict = None) -> 'Bus':
        """
        从XML元素中解析母线模型

        参数:
            element: XML元素
            ns: 命名空间映射
            analog_channels: 模拟通道字典（可选），用于解析ACVBranch中的通道对象
            status_channels: 开关量通道字典（可选），用于解析开关量通道对象
            
        返回:
            Bus: 母线实例
        """
        idx = parse_int(element.get('idx', 1))
        bus_name = element.get('bus_name', "")
        src_ref = element.get('srcRef', "")
        v_rtg = parse_float(element.get('VRtg', 0.0))
        v_rtg_snd = parse_float(element.get('VRtgSnd', 100.0))
        v_rtg_snd_pos_str = element.get('VRtgSnd_Pos', "")
        v_rtg_snd_pos = TvInstallSite.from_value(v_rtg_snd_pos_str, default=TvInstallSite.BUS)
        bus_uuid = element.get('bus_uuid', "")
        bus = cls(index=idx, name=bus_name, reference=src_ref, v_rtg=v_rtg, v_rtg_snd=v_rtg_snd,
                  v_rtg_snd_pos=v_rtg_snd_pos, uuid=bus_uuid)

        # 查找 ACVChn 元素（支持带/不带命名空间）
        acv_chn_elem = element.find('scl:ACVChn', ns) if 'scl' in ns else None
        if acv_chn_elem is None:
            acv_chn_elem = element.find('ACVChn')
        if acv_chn_elem is not None:
            bus.voltage = ACVBranch.from_xml(acv_chn_elem, ns, analog_channels=analog_channels)

        # 解析通道（支持带/不带命名空间）
        if 'scl' in ns:
            bus.anas = cls.parse_ans_from_xml(element, ns, analog_channels=analog_channels, use_scl_prefix=True)
            bus.stas = cls.parse_sts_from_xml(element, ns, status_channels=status_channels, use_scl_prefix=True)
        else:
            bus.anas = cls.parse_ans_from_xml(element, ns, analog_channels=analog_channels, use_scl_prefix=False)
            bus.stas = cls.parse_sts_from_xml(element, ns, status_channels=status_channels, use_scl_prefix=False)

        return bus
