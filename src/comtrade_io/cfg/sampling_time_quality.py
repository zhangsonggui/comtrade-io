#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel, Field, field_validator


class SamplingTimeQuality(BaseModel):
    """采样时间品质模型（tmq_code 与 lcapsec）

    tmq_code: 4-bit 16 进制码，代表时钟质量等级
    lcapsec: 闰秒指示，取值 0-3
    附带解码方法 decode()，可将 tmq_code 解析为可读的时钟质量信息。
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
        """序列化为逗号分隔的字符串

        将采样时间品质对象转换为COMTRADE配置文件格式的字符串。

        Returns:
            str: 逗号分隔的字符串，格式为 "tmq_code,lcapsec"
        """
        return f"{self.tmq_code},{self.lcapsec}"

    @property
    def decode(self) -> dict:
        """解码tmq_code，返回结构化信息字典

        将16进制的时间质量码解析为可读的时钟质量信息。
        解析内容包括：二进制表示、整数值、是否锁定、精度和描述信息。

        Returns:
            dict: 包含以下键的字典:
                - tmq_code: 原始时间质量码
                - binary: 4位二进制表示
                - value: 整数值
                - locked: 是否锁定
                - precision_seconds: 精度（秒）
                - description: 描述信息
        """
        code_int = int(self.tmq_code, 16)
        # 4 位二进制表示
        bin4 = format(code_int, '04b')
        value = code_int
        # 默认字段
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
                    exp = 10 - value  # 1->9, 9->1 的指数关系
                    precision = 10 ** (-exp)
                    description = f'时钟未锁定，误差 10^-{exp} s 以内'
                else:
                    mag = 10 ** (value - 10)
                    precision = mag
                    description = f'时钟未锁定，误差 10^{value - 10} s 以内'
            else:
                # 保守兜底
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

    @classmethod
    def from_str(cls, _str: str) -> 'SamplingTimeQuality':
        """从逗号分隔的字符串反序列化采样时间品质

        将配置文件中的采样时间品质字符串解析为SamplingTimeQuality对象。

        参数:
            _str: 逗号分隔的字符串，如 "F,1"

        Returns:
            SamplingTimeQuality: 解析后的采样时间品质对象

        异常:
            ValueError: 当字符串格式不正确或字段长度不符合要求时抛出
        """
        from comtrade_io.utils.str_split import str_split
        parts = str_split(_str)
        if len(parts) < 2:
            raise ValueError(f"字符串分割后数组为[{parts}],长度不足")
        return cls(tmq_code=parts[0], lcapsec=int(parts[1]))

    @classmethod
    def from_dict(cls, data: dict) -> 'SamplingTimeQuality':
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> 'SamplingTimeQuality':
        import json
        data = json.loads(json_str)
        return cls.from_dict(data)
