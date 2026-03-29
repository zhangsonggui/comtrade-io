#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel, Field

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


class TransformerSection(BaseModel):
    """主变部件模型"""
    area: str = "private"
    index: int = Field(default=0, description="主变编号")
    name: str = Field(default="主变名称", description="主变名称")
    capacity: float = Field(default=0.0, description="变压器额定功率")
    winding_num: int = Field(default=3, description="绕组数量")
    high_wind_flag: str = Field(default="Y", description="高压侧绕组接线")
    high_rated_primary_voltage: float = Field(default=220.0, description="高压侧一次额定电压")
    high_bran_num: int = Field(default=1, description="高压侧分路数")
    high_voltage_indexes: list[int] = Field(default_factory=list, description="高压侧电压通道索引")
    high_current_indexes: list[int] = Field(default_factory=list, description="高压侧电流通道索引")
    medium_wind_flag: str = Field(default="Y12", description="中压侧绕组接线")
    medium_rated_primary_voltage: float = Field(default=220.0, description="中压侧一次额定电压")
    medium_bran_num: int = Field(default=1, description="中压侧分路数")
    medium_voltage_indexes: list[int] = Field(default_factory=list, description="中压侧电压通道索引")
    medium_current_indexes: list[int] = Field(default_factory=list, description="中压侧电流通道索引")
    low_wind_flag: str = Field(default="D11", description="低压侧绕组接线")
    low_rated_primary_voltage: float = Field(default=220.0, description="低压侧一次额定电压")
    low_bran_num: int = Field(default=1, description="低压侧分路数")
    low_voltage_indexes: list[int] = Field(default_factory=list, description="高压侧电压通道索引")
    low_current_indexes: list[int] = Field(default_factory=list, description="高压侧电流通道索引")
    status_indexes: list[int] = Field(default_factory=list, description="开关量通道索引")

    def from_str(self, content: str):
        pass

    @classmethod
    def from_dict(cls, data: dict):
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
        capacity = parse_number_with_unit(data.get('CAPACITY', '0'))

        # 解析绕组数量
        winding_num = int(data.get('WINDING_NUM', '3'))

        # 解析高压侧参数 H_PARAM: 接线, 电压, 分路数
        h_param = data.get('H_PARAM', 'Y, 220, 1')
        high_wind_flag, high_rated_primary_voltage, high_bran_num = parse_param(h_param)
        high_voltage_indexes = parse_indexes(data.get('H_TV_CHNS', ''))

        # 解析中压侧参数 M_PARAM
        m_param = data.get('M_PARAM', 'Y12, 110, 1')
        medium_wind_flag, medium_rated_primary_voltage, medium_bran_num = parse_param(m_param)
        medium_voltage_indexes = parse_indexes(data.get('M_TV_CHNS', ''))

        # 解析低压侧参数 L_PARAM
        l_param = data.get('L_PARAM', 'D11, 10, 1')
        low_wind_flag, low_rated_primary_voltage, low_bran_num = parse_param(l_param)
        low_voltage_indexes = parse_indexes(data.get('L_TV_CHNS', ''))

        # 解析电流通道索引 (TA_Id_#1, TA_Id_#3, TA_Id_#5)
        high_current_indexes = []
        medium_current_indexes = []
        low_current_indexes = []

        for key, value in data.items():
            if key.startswith('TA_Id_#'):
                parts = [p.strip() for p in value.split(',')]
                if len(parts) >= 3:
                    indexes = [int(parts[0]), int(parts[1]), int(parts[2])]
                    section_num = key.split('#')[1]
                    if section_num in ['1', '2']:
                        high_current_indexes.extend(indexes)
                    elif section_num in ['3', '4']:
                        medium_current_indexes.extend(indexes)
                    elif section_num in ['5', '6']:
                        low_current_indexes.extend(indexes)

        # 解析状态通道
        status_indexes = parse_indexes(data.get('STATUS_CHNS', ''))

        _transformer_section = {
            'area'                        : data.get('area'),
            'index'                       : int(data.get('index', 0)),
            'name'                        : data.get('DEV_ID'),
            'capacity'                    : capacity,
            'winding_num'                 : winding_num,
            'high_wind_flag'              : high_wind_flag,
            'high_rated_primary_voltage'  : high_rated_primary_voltage,
            'high_bran_num'               : high_bran_num,
            'high_voltage_indexes'        : high_voltage_indexes,
            'high_current_indexes'        : high_current_indexes,
            'medium_wind_flag'            : medium_wind_flag,
            'medium_rated_primary_voltage': medium_rated_primary_voltage,
            'medium_bran_num'             : medium_bran_num,
            'medium_voltage_indexes'      : medium_voltage_indexes,
            'medium_current_indexes'      : medium_current_indexes,
            'low_wind_flag'               : low_wind_flag,
            'low_rated_primary_voltage'   : low_rated_primary_voltage,
            'low_bran_num'                : low_bran_num,
            'low_voltage_indexes'         : low_voltage_indexes,
            'low_current_indexes'         : low_current_indexes,
            'status_indexes'              : status_indexes
        }
        return cls(**_transformer_section)
