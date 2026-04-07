#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel, Field

from comtrade_io.inf.section_base_model import SectionBaseModel
from comtrade_io.type import TransWindLocation

trans_dict = {'CAPACITY'   : '180(MVA)',
              'DEV_ID'     : '20,主变A套',
              'H_PARAM'    : 'Y, 220.000(KV), 1',
              'H_TV_CHNS'  : '7, 8, 9, 0',
              'L_PARAM'    : 'D11, 10.000(KV), 1',
              'L_TV_CHNS'  : '35, 36, 37, 0',
              'M_PARAM'    : 'Y12, 110.000(KV), 1',
              'M_TV_CHNS'  : '21, 22, 23, 0',
              'OBJECT_TYPE': 'MAIN',
              'STATUS_CHNS': '1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20',
              'SYS_ID'     : '',
              'TA_Id_#1'   : '1, 2, 3, 1',
              'TA_Id_#3'   : '15, 16, 17, 1',
              'TA_Id_#5'   : '29, 30, 31, 1',
              'WINDING_NUM': '3',
              'area'       : 'ZYHD',
              'index'      : 1,
              'type'       : 'Transformer'}


class TransformerWindingSection(BaseModel):
    trans_wind_location: TransWindLocation = Field(default=TransWindLocation.HIGH, description="绕组位置")
    wind_flag: str = Field(default="Y", description="绕组接线")
    rated_primary_voltage: float = Field(default=220.0, description="一次额定电压")
    bran_num: int = Field(default=1, description="电流通道分路数")
    voltage_indexes: list[int] = Field(default_factory=list, description="电压通道索引")
    current_indexes: list[list[int]] = Field(default_factory=list, description="电流通道索引")

    @classmethod
    def from_dict(cls, data: dict, location_prefix: str = 'H_'):
        if location_prefix == 'M_':
            twl = TransWindLocation.MEDIUM
            ci1 = data.get('TA_Id_#1', "")
            ci2 = data.get('TA_Id_#2', "")
        elif location_prefix == 'L_':
            twl = TransWindLocation.LOW
            ci1 = data.get('TA_Id_#3', "")
            ci2 = data.get('TA_Id_#4', "")
        else:
            twl = TransWindLocation.HIGH
            ci1 = data.get('TA_Id_#5', "")
            ci2 = data.get('TA_Id_#6', "")
        location_data = {k[len(location_prefix):]: v for k, v in data.items() if k.startswith(location_prefix)}
        param = location_data.get('PARAM', 'Y, 220, 1')
        parts = [p.strip() for p in param.split(',')]
        wind_flag = parts[0] if len(parts) > 0 else 'Y'
        match = re.search(r'\d+\.?\d*', parts[1]) if len(parts) > 1 else 220
        rated_primary_voltage = float(match.group()) if match else 0.0
        bran_num = int(parts[2]) if len(parts) > 2 else 1
        tv_chns = data.get('H_TV_CHNS', '')
        voltage_indexes = [int(i.strip()) for i in tv_chns.split(',') if i.strip()]
        current_indexes = [[int(i.strip()) for i in ci1.split(',') if i.strip()]]
        if ci2 != '':
            current_indexes.append([int(i.strip()) for i in ci2.split(',') if i.strip()])
        return cls(trans_wind_location=twl,
                   wind_flag=wind_flag,
                   rated_primary_voltage=rated_primary_voltage,
                   bran_num=bran_num,
                   voltage_indexes=voltage_indexes,
                   current_indexes=current_indexes
                   )


class TransformerSection(SectionBaseModel):
    """主变部件模型"""
    capacity: float = Field(default=0.0, description="变压器额定功率")
    winding_num: int = Field(default=3, description="绕组数量")
    trans_winds: list[TransformerWindingSection] = Field(default_factory=list, description="变压器绕组")

    @classmethod
    def from_dict(cls, data: dict):
        ts = super().from_dict(data)

        def parse_number_with_unit(s: str) -> float:
            match = re.search(r'\d+\.?\d*', s)
            return float(match.group()) if match else 0.0

        def parse_param(s: str) -> tuple[str, float, int]:
            parts = [p.strip() for p in s.split(',')]
            wind_flag = parts[0] if len(parts) > 0 else 'Y'
            voltage = parse_number_with_unit(parts[1]) if len(parts) > 1 else 0.0
            bran_num = int(parts[2]) if len(parts) > 2 else 1
            return wind_flag, voltage, bran_num

        def parse_indexes(s: str) -> list[int]:
            return [int(i.strip()) for i in s.split(',') if i.strip()]

        # 解析额定容量
        ts.capacity = parse_number_with_unit(data.get('CAPACITY', '0'))

        # 解析绕组数量
        ts.winding_num = int(data.get('WINDING_NUM', '3'))

        # 解析高压侧
        high_wind = TransformerWindingSection.from_dict(data, 'H_')
        ts.trans_winds.append(high_wind)

        # 解析中压侧
        medium_wind = TransformerWindingSection.from_dict(data, 'M_')
        ts.trans_winds.append(medium_wind)

        # 解析低压侧参数 L_PARAM
        low_wind = TransformerWindingSection.from_dict(data, 'L_')
        ts.trans_winds.append(low_wind)

        return ts
