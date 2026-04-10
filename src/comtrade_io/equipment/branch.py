#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分支通道模块

定义交流电压分支和交流电流分支类，用于表示电力系统中电压和电流通道的关联关系。
ACVBranch用于表示电压通道组，ACCBranch用于表示电流通道组。
"""

from typing import Optional
from xml.etree.ElementTree import Element

from pydantic import BaseModel, Field

from comtrade_io.dmf.analog_channel import AnalogChannel
from comtrade_io.type import CtDirection, Phase
from comtrade_io.utils import parse_int


class ACVBranch(BaseModel):
    """
    交流电压分支类

    表示一组交流电压通道的关联关系，包含A、B、C、N、L相的电压通道。
    用于在电力系统模型中将多个电压通道关联到一个电气设备。

    实例化时可以传入通道索引和analog_channels字典，会自动解析为AnalogChannel对象。
    也可以直接传入AnalogChannel对象。

    属性:
        ua: A相电压通道
        ub: B相电压通道
        uc: C相电压通道
        un: N相（零序）电压通道
        ul: L相电压通道（线电压）
    """

    ua: Optional[AnalogChannel] = Field(default=None, description="A相电压通道")
    ub: Optional[AnalogChannel] = Field(default=None, description="B相电压通道")
    uc: Optional[AnalogChannel] = Field(default=None, description="C相电压通道")
    un: Optional[AnalogChannel] = Field(default=None, description="N相电压通道")
    ul: Optional[AnalogChannel] = Field(default=None, description="L相电压通道")

    def __str__(self):
        """
        返回交流电压分支的XML字符串表示形式

        返回:
            格式化的XML字符串，表示交流电压分支的所有通道索引
        """
        attrs = []
        if self.ua:
            attrs.append(f'ua_idx="{self.ua.index}"')
        if self.ub:
            attrs.append(f'ub_idx="{self.ub.index}"')
        if self.uc:
            attrs.append(f'uc_idx="{self.uc.index}"')
        if self.un:
            attrs.append(f'un_idx="{self.un.index}"')
        if self.ul:
            attrs.append(f'ul_idx="{self.ul.index}"')

        if not attrs:
            return f"<scl:ACVBranch />"

        xml = f"<scl:ACVBranch {' '.join(attrs)} />"
        return xml

    @classmethod
    def from_xml(
            cls, element: Element, ns: dict = None, analog_channels: dict = None
    ) -> "ACVBranch":
        """
        从XML元素中解析交流电压分支

        参数:
            element: XML元素
            ns: 命名空间映射（可选）
            analog_channels: 模拟通道字典（可选），用于解析通道对象

        返回:
            ACVBranch: 交流电压分支实例
        """
        ua_idx = parse_int(element.get("ua_idx", 0))
        ub_idx = parse_int(element.get("ub_idx", 0))
        uc_idx = parse_int(element.get("uc_idx", 0))
        ul_idx = parse_int(element.get("ul_idx", 0))
        un_idx = parse_int(element.get("un_idx", 0))

        if analog_channels is None:
            return cls()
        kwargs = {}
        if ua_idx:
            kwargs["ua"] = analog_channels.get(ua_idx, None)
        if ub_idx:
            kwargs["ub"] = analog_channels.get(ub_idx, None)
        if uc_idx:
            kwargs["uc"] = analog_channels.get(uc_idx, None)
        if ul_idx:
            kwargs["ul"] = analog_channels.get(ul_idx, None)
        if un_idx:
            kwargs["un"] = analog_channels.get(un_idx, None)

        return cls(**kwargs)

    @classmethod
    def from_analog_channels(
            cls, analog_channels: list[AnalogChannel]
    ) -> "ACVBranch":
        """
        根据模拟通道列表自动生成ACVBranch实例

        该方法根据analog_channels中各通道的相别(phase)属性，
        自动将通道分配到对应的属性:
        - A相 -> ua
        - B相 -> ub
        - C相 -> uc
        - N相 -> un
        - L相 -> ul

        参数:
            analog_channels: 模拟通道列表

        返回:
            ACVBranch: 交流电压分支实例
        """
        kwargs = {}
        phase_map = {
            Phase.PHASE_A: "ua",
            Phase.PHASE_B: "ub",
            Phase.PHASE_C: "uc",
            Phase.PHASE_N: "un",
            Phase.PHASE_L: "ul",
        }

        for channel in analog_channels:
            if channel is None:
                continue
            if channel.phase in phase_map:
                attr_name = phase_map[channel.phase]
                kwargs[attr_name] = channel

        return cls(**kwargs)


class ACCBranch(BaseModel):
    """
    交流电流分支类

    表示一组交流电流通道的关联关系，包含A、B、C、N相的电流通道和电流方向。
    用于在电力系统模型中将多个电流通道关联到一个电气设备或线路段。

    实例化时可以传入通道索引和analog_channels字典，会自动解析为AnalogChannel对象。
    也可以直接传入AnalogChannel对象。

    属性:
        idx: 分支序号，用于标识不同的电流分支
        ia: A相电流通道
        ib: B相电流通道
        ic: C相电流通道
        i0: N相（零序）电流通道
        dir: 电流方向，标识功率流动方向（正向/反向）
    """

    idx: int = Field(default=None, description="分支序号")
    ia: Optional[AnalogChannel] = Field(default=None, description="A相电流通道")
    ib: Optional[AnalogChannel] = Field(default=None, description="B相电流通道")
    ic: Optional[AnalogChannel] = Field(default=None, description="C相电流通道")
    i0: Optional[AnalogChannel] = Field(default=None, description="N相电流通道")
    dir: CtDirection = Field(default=CtDirection.POS, description="电流方向")

    def __str__(self):
        """
        返回交流电流分支的XML字符串表示形式

        返回:
            格式化的XML字符串，表示交流电流分支的所有属性
        """
        attrs = []
        if self.idx is not None:
            attrs.append(f'idx="{self.idx}"')
        if self.ia is not None:
            attrs.append(f'ia_idx="{self.ia.index}"')
        if self.ib is not None:
            attrs.append(f'ib_idx="{self.ib.index}"')
        if self.ic is not None:
            attrs.append(f'ic_idx="{self.ic.index}"')
        if self.i0 is not None:
            attrs.append(f'in_idx="{self.i0.index}"')
        if self.dir is not None:
            attrs.append(f'dir="{self.dir.value}"')

        if not attrs:
            return f"<scl:ACC_Bran />"

        xml = f"<scl:ACC_Bran {' '.join(attrs)} />"
        return xml

    @classmethod
    def from_xml(
            cls, element: Element, ns: dict = None, analog_channels: dict = None
    ) -> "ACCBranch":
        """
        从XML元素中解析交流电流分支

        参数:
            element: XML元素
            ns: 命名空间映射（可选）
            analog_channels: 模拟通道字典（可选），用于解析通道对象

        返回:
            ACCBranch: 交流电流分支实例
        """
        ct_direction = element.get("dir", "")
        idx = parse_int(element.get("bran_idx", 0))
        ia_idx = parse_int(element.get("ia_idx", 0))
        ib_idx = parse_int(element.get("ib_idx", 0))
        ic_idx = parse_int(element.get("ic_idx", 0))
        in_idx = parse_int(element.get("in_idx", 0))
        dir_val = CtDirection.from_value(ct_direction, CtDirection.POS)

        if analog_channels is None:
            return cls(idx=idx, dir=dir_val)

        kwargs = {"idx": idx, "dir": dir_val}
        if ia_idx:
            kwargs["ia"] = analog_channels.get(ia_idx, None)
        if ib_idx:
            kwargs["ib"] = analog_channels.get(ib_idx, None)
        if ic_idx:
            kwargs["ic"] = analog_channels.get(ic_idx, None)
        if in_idx:
            kwargs["i0"] = analog_channels.get(in_idx, None)

        return cls(**kwargs)

    @classmethod
    def from_analog_channels(
            cls, analog_channels: list[AnalogChannel]
    ) -> "ACCBranch":
        """
        根据模拟通道列表自动生成ACCBranch实例

        该方法根据analog_channels中各通道的相别(phase)属性，
        自动将通道分配到对应的属性:
        - A相 -> ia
        - B相 -> ib
        - C相 -> ic
        - N相 -> i0

        参数:
            analog_channels: 模拟通道列表

        返回:
            ACCBranch: 交流电流分支实例
        """
        kwargs = {}
        phase_map = {
            Phase.PHASE_A: "ia",
            Phase.PHASE_B: "ib",
            Phase.PHASE_C: "ic",
            Phase.PHASE_N: "i0",
        }

        for channel in analog_channels:
            if channel.phase in phase_map:
                attr_name = phase_map[channel.phase]
                kwargs[attr_name] = channel

        return cls(**kwargs)
