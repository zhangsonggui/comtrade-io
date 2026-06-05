#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel

from comtrade_io.model.channel import Analog, Status
from comtrade_io.model.equipment import Transformer
from comtrade_io.model.equipment.branch import ACCBranch, ACVBranch
from comtrade_io.model.equipment.transformer_winding import (
    TransformerWinding,
    WindGroup,
)
from comtrade_io.model.type import CurrentBranchNum, TransWindLocation
from comtrade_io.parser.inf.equipment_section import (
    EquipmentSection,
    parse_number_with_unit,
    str2channel,
)
from comtrade_io.utils import get_logger

logger = get_logger()

class TransformerWindingSection(BaseModel):
    """变压器绕组部件解析

    解析变压器单个绕组（高压 H_ / 中压 M_ / 低压 L_）的参数：
    - PARAM: 绕组参数（接线组别、额定电压、档位）
    - TV_CHNS: 电压通道引用
    - TA_Id: 电流通道引用
    """

    @classmethod
    def from_dict(cls, data: dict, analog_channels: dict[int, Analog],
                  location_prefix: str = 'H_') -> TransformerWinding:
        """从字典创建变压器绕组对象

        根据 location_prefix 确定绕组位置（H_ 高压 / M_ 中压 / L_ 低压），
        解析该绕组的电压/电流通道和电气参数。

        参数:
            data: 变压器节键值对
            analog_channels: 模拟通道字典
            location_prefix: 绕组位置前缀，默认为 H_（高压侧）

        返回:
            TransformerWinding: 变压器绕组对象
        """
        if location_prefix == 'M_':
            twl = TransWindLocation.MEDIUM
            current_1 = str2channel(data.get('TA_Id_#1', ""), analog_channels)
            current_2 = str2channel(data.get('TA_Id_#2', ""), analog_channels)
            voltage = str2channel(data.get('M_TV_CHNS', ""), analog_channels)
        elif location_prefix == 'L_':
            twl = TransWindLocation.LOW
            current_1 = str2channel(data.get('TA_Id_#3', ""), analog_channels)
            current_2 = str2channel(data.get('TA_Id_#4', ""), analog_channels)
            voltage = str2channel(data.get('L_TV_CHNS', ""), analog_channels)
        else:
            twl = TransWindLocation.HIGH
            current_1 = str2channel(data.get('TA_Id_#5', ""), analog_channels)
            current_2 = str2channel(data.get('TA_Id_#6', ""), analog_channels)
            voltage = str2channel(data.get('H_TV_CHNS', ""), analog_channels)
        location_data = {k[len(location_prefix):]: v for k, v in data.items() if k.startswith(location_prefix)}
        param = location_data.get('PARAM', 'Y, 220, 1')
        parts = [p.strip() for p in param.split(',')]
        wind_flag_str = parts[0] if len(parts) > 0 else 'Y'
        wind_group = WindGroup.from_str(wind_flag_str)
        match = re.search(r'\d+\.?\d*', parts[1]) if len(parts) > 1 else 220
        rated_primary_voltage = float(match.group()) if match else 0.0
        currents = []
        if current_1:
            currents.extend(ACCBranch.from_analog_channels(current_1))
        if current_2:
            currents.extend(ACCBranch.from_analog_channels(current_2))
        bran_num = CurrentBranchNum.B2 if len(currents) > 1 else CurrentBranchNum.B1

        return TransformerWinding(trans_wind_location=twl,
                                  wind_group=wind_group,
                                  voltage=ACVBranch.from_analog_channels(voltage),
                                  currents=currents,
                                  bran_num=bran_num,
                                  rated_voltage=rated_primary_voltage
                                  )


class TransformerSection(EquipmentSection):
    """主变压器部件解析

    继承 EquipmentSection，增加变压器特有属性：
    - CAPACITY: 额定容量
    - WINDING_NUM: 绕组数量
    - H_ / M_ / L_: 各绕组参数（委托 TransformerWindingSection 解析）
    """

    @classmethod
    def from_dict(cls,
                  data: dict,
                  analog_channels: dict[int, Analog],
                  status_channels: dict[int, Status]) -> 'Transformer':
        """从字典生成变压器模型

        解析额定容量、绕组数量，并依次解析高压/中压/低压绕组的详细参数。
        各绕组的电压和电流通道会自动合并到变压器的 acvs / accs 中。

        参数:
            data: 变压器节键值对
            analog_channels: 模拟通道字典
            status_channels: 开关量通道字典

        返回:
            Transformer: 变压器对象，含所有绕组信息
        """
        equipment = super().from_dict(data, analog_channels, status_channels)
        transformer = Transformer(index=equipment.index,
                                  uuid=equipment.uuid,
                                  name=equipment.name,
                                  stas=equipment.stas,
                                  acvs=equipment.acvs,
                                  accs=equipment.accs)

        # 解析额定容量
        transformer.capacity = parse_number_with_unit(data.get('CAPACITY', '0'))

        # 解析绕组数量
        transformer.winding_num = int(data.get('WINDING_NUM', '3'))

        for location in ('H_', 'M_', 'L_'):
            wind = TransformerWindingSection.from_dict(data, analog_channels, location)
            if wind is None:
                continue
            for voltage in (wind.voltage.ua, wind.voltage.ub, wind.voltage.uc, wind.voltage.un, wind.voltage.ul):
                if voltage:
                    transformer.acvs.append(voltage)
            for current in wind.currents:
                for cb in (current.ia, current.ib, current.ic, current.i0):
                    if cb:
                        transformer.accs.append(cb)
            transformer.trans_winds.append(wind)

        logger.debug(
            f"变压器 {equipment.index}: {equipment.name}, "
            f"容量={transformer.capacity}MVA, 绕组数={transformer.winding_num}"
        )
        return transformer
