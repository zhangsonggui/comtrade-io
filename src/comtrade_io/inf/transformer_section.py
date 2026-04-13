#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel

from comtrade_io.channel import Analog, Status
from comtrade_io.equipment import Transformer
from comtrade_io.equipment.branch import ACCBranch, ACVBranch
from comtrade_io.equipment.transformer_winding import TransformerWinding, WindGroup
from comtrade_io.inf.equipment_section import EquipmentSection, parse_number_with_unit, str2channel
from comtrade_io.type import CurrentBranchNum, TransWindLocation


class TransformerWindingSection(BaseModel):
    """变压器绕组部件模型"""

    @classmethod
    def from_dict(cls, data: dict, analog_channels: dict[int, Analog],
                  location_prefix: str = 'H_') -> TransformerWinding:
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
    """主变部件模型"""

    @classmethod
    def from_dict(cls,
                  data: dict,
                  analog_channels: dict[int, Analog],
                  status_channels: dict[int, Status]) -> 'Transformer':
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

        return transformer
