#!/usr/bin/env python
# -*- coding: utf-8 -*-
from xml.etree.ElementTree import Element

from comtrade_io.channel.analog import Analog
from comtrade_io.type import (AnalogChannelFlag, AnalogChannelType, Phase, TranSide, Unit)
from comtrade_io.utils import parse_float, parse_int


class AnalogElement:

    @classmethod
    def from_xml(cls, element: Element) -> Analog:
        """从XML元素创建AnalogChannel实例

        参数:
            element (Element): XML元素
            ns (dict, optional): 命名空间映射
            analog (Analog, optional): 用于对比和更新的Analog实例

        返回:
            AnalogChannel: AnalogChannel实例
        """
        _type = AnalogChannelType.from_value(element.get('type', ''))
        _flag = AnalogChannelFlag.from_value(element.get('flag', ''))
        if _type != _flag.type:
            _type = _flag.type
        _unit_str = element.get('sIUnit', '')
        _phase_str = element.get('ph', '')
        _tran_side_str = element.get('ps', '')
        return Analog(
                index=parse_int(element.get('idx_cfg', 1)),
                idx_org=parse_int(element.get('idx_org', 1)),
                type=_type,
                flag=_flag,
                primary_min_value=parse_float(element.get('p_min', 0.0)),
                primary_max_value=parse_float(element.get('p_max', 0.0)),
                secondary_min_value=parse_float(element.get('s_min', 0.0)),
                secondary_max_value=parse_float(element.get('s_max', 0.0)),
                freq=parse_float(element.get('freq', 50.0)),
                au=parse_float(element.get('au', 1.0)),
                bu=parse_float(element.get('bu', 0.0)),
                unit=Unit.from_value(_unit_str),
                unit_multiplier=element.get('multiplier', ""),
                phase=Phase.from_value(_phase_str),
                primary=parse_float(element.get('primary', 1.0)),
                secondary=parse_float(element.get('secondary', 1.0)),
                tran_side=TranSide.from_value(_tran_side_str)
        )
