#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field


class SectionBaseModel(BaseModel):
    """部件基类"""
    area: str = Field(default="private", description="所属区域段")
    index: int = Field(default=0, description="编号")
    name: str = Field(default="名称", description="设备名称")
    voltage_indexes: list[int] = Field(default_factory=list, description="电压通道索引")
    status_indexes: list[int] = Field(default_factory=list, description="开关量通道索引")

    @staticmethod
    def parse_indexes(s: str) -> list[int]:
        indexes = [int(i.strip()) for i in s.split(',') if i.strip()]
        result = []
        prev = None
        for i in indexes:
            if prev is None or i >= prev:
                result.append(i)
                prev = i
            else:
                break
        return result

    @classmethod
    def from_dict(cls, data: dict):
        name_str = data.get('DEV_ID')
        _, name = name_str.split(',')

        return cls(**{
            'area'           : data.get('area'),
            'index'          : int(data.get('index', 0)),
            'name'           : name,
            'voltage_indexes': cls.parse_indexes(data.get('TV_CHNS', '')),
            'status_indexes' : cls.parse_indexes(data.get('STATUS_CHNS', ''))
        })
