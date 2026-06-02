#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel, Field, field_validator


class SamplingTimeQuality(BaseModel):
    """采样时间品质模型（tmq_code 与 lcapsec）

    tmq_code: 4-bit 16 进制码，代表时钟质量等级
    lcapsec: 闰秒指示，取值 0-3
    """
    tmq_code: str = Field(..., description="tmq_code, hex digits, 1-4 chars")
    lcapsec: int = Field(..., description="leap second indicator, 0-3")

    @field_validator('tmq_code')
    def _validate_tmq_code(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("tmq_code must be a string")
        if len(v) < 1 or len(v) > 4:
            raise ValueError("tmq_code length must be between 1 and 4")
        if not re.match(r'^[0-9A-Fa-f]+$', v):
            raise ValueError("tmq_code must be hex digits")
        return v.upper()

    @field_validator('lcapsec')
    def _validate_lcapsec(cls, v: int) -> int:
        if not isinstance(v, int):
            raise ValueError("lcapsec must be int")
        if v < 0 or v > 3:
            raise ValueError("lcapsec must be in 0..3")
        return v

    def __str__(self) -> str:
        return f"{self.tmq_code},{self.lcapsec}"

    @property
    def decode(self) -> dict:
        """解码tmq_code，返回结构化信息字典"""

        code_int = int(self.tmq_code, 16)
        bin4 = format(code_int, '04b')
        value = code_int
        description = ''
        precision = None
        locked = True if value == 0 else False
        if value == 0:
            description = '时钟未锁定，正常运行，时钟锁定'
            precision = 0.0
        elif value == 0xF:
            description = '时钟错乱，时间不可置信'
            precision = None
        else:
            locked = False
            if 1 <= value <= 14:
                if value <= 9:
                    exp = 10 - value
                    precision = 10 ** (-exp)
                    description = f'时钟未锁定，误差 10^-{exp} s 以内'
                else:
                    mag = 10 ** (value - 10)
                    precision = mag
                    description = f'时钟未锁定，误差 10^{value - 10} s 以内'
            else:
                precision = None
                description = '未知的时间质量码'
        return {
            'tmq_code'         : self.tmq_code,
            'binary'           : bin4,
            'value'            : value,
            'locked'           : locked,
            'precision_seconds': precision,
            'description'      : description,
        }
