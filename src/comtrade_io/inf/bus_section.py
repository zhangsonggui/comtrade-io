#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import Field

from comtrade_io.inf.section_base_model import SectionBaseModel
from comtrade_io.type import TvInstallSite

bus_dict = {'DEV_ID'     : '7,220kV 602大晃线第一套合并单元电压',
            'RATED_VALUE': '220000V',
            'SYS_ID'     : '',
            'TV_CHNS'    : '46,47,48,0',
            'TV_POS'     : 'Line',
            'TV_RATIO'   : '220kV/100V',
            'area'       : 'ZYHD',
            'index'      : 1,
            'type'       : 'Bus'}


class BusSection(SectionBaseModel):
    """母线部件模型"""
    rated_primary_voltage: float = Field(default=220.0, description="一次额定电压（kV）")
    rated_secondary_voltage: float = Field(default=100.0, description="二次额定电压（V）")
    tv_install_site: TvInstallSite = Field(default=TvInstallSite.BUS, description="电压互感器安装位置")


    @classmethod
    def from_dict(cls, data: dict):
        bs = super().from_dict(data)
        _tv_ratio = data.get('TV_RATIO', "220kV/100V")
        _tv_pos = data.get('TV_POS', "BUS")

        primary_voltage = 220.0
        secondary_voltage = 100.0

        if '/' in _tv_ratio:
            parts = _tv_ratio.split('/')
            first_part = parts[0]
            second_part = parts[1] if len(parts) > 1 else ''

            # 解析一次电压
            primary_match = re.search(r'\d+\.?\d*', first_part)
            if primary_match:
                primary_value = float(primary_match.group())
                # 检查单位是否为V或数值大于10000
                if 'V' in first_part and 'kV' not in first_part:
                    primary_voltage = primary_value / 1000
                elif primary_value > 10000:
                    primary_voltage = primary_value / 1000
                else:
                    primary_voltage = primary_value

            # 解析二次电压
            secondary_match = re.search(r'\d+\.?\d*', second_part)
            secondary_voltage = float(secondary_match.group()) if secondary_match else 100.0
        bs.rated_primary_voltage = primary_voltage
        bs.rated_secondary_voltage = secondary_voltage
        bs.tv_install_site = TvInstallSite.BUS if _tv_pos == 'BUS' else TvInstallSite.LINE
        return bs
