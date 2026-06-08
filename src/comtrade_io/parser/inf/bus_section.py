#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from comtrade_io.model.channel import Analog, Status
from comtrade_io.model.equipment import Bus
from comtrade_io.model.type import TvInstallSite
from comtrade_io.parser.inf.equipment_section import EquipmentSection
from comtrade_io.utils import get_logger

logger = get_logger()

class BusSection(EquipmentSection):
    """母线部件解析

    继承 EquipmentSection，增加母线特有的属性解析：
    - TV_RATIO: 电压互感器变比（如 "220kV/100V"）
    - TV_POS: 电压互感器位置（BUS / LINE）
    - 额定一次/二次电压
    """

    @classmethod
    def from_dict(cls,
                  data: dict,
                  analog_channels: dict[int, Analog],
                  status_channels: dict[int, Status]) -> Bus:
        """从字典生成母线模型

        除基类解析的设备共性外，额外解析 TV_RATIO 计算额定电压。

        参数:
            data: 母线节键值对
            analog_channels: 模拟通道字典
            status_channels: 开关量通道字典

        返回:
            Bus: 母线对象，含额定电压和 TV 安装位置
        """
        equipment = super().from_dict(data, analog_channels, status_channels)
        bus = Bus(index=equipment.index,
                  uuid=equipment.uuid,
                  name=equipment.name,
                  stas=equipment.stas,
                  acvs=equipment.acvs,
                  accs=equipment.accs)
        tv_ratio = data.get('TV_RATIO', "220kV/100V")
        tv_pos = data.get('TV_POS', "BUS")
        bus.tv_install_site = TvInstallSite.BUS if tv_pos == 'BUS' else TvInstallSite.LINE

        primary_voltage = 220.0
        secondary_voltage = 100.0

        if '/' in tv_ratio:
            parts = tv_ratio.split('/')
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
        bus.rated_primary_voltage = primary_voltage
        bus.rated_secondary_voltage = secondary_voltage

        logger.debug(
            f"母线 {equipment.index}: {equipment.name}, 额定电压={primary_voltage}kV"
        )
        return bus
