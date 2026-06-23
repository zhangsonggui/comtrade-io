#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pydantic import BaseModel, Field, field_validator


class SamplingTimeQuality(BaseModel):
    """采样时间品质模型（tmq_code 与 lcapsec）

    tmq_code: 0-F 十六进制码，代表时钟质量等级
    lcapsec: 闰秒指示，取值 0-3
    """

    tmq_code: str = Field(default="0", description="tmq_code, hex digit, 0-F")
    lcapsec: int = Field(default=0, description="leap second indicator, 0-3")

    @field_validator("tmq_code")
    def _validate_tmq_code(cls, v: str) -> str:
        if not isinstance(v, str):
            raise ValueError("tmq_code must be a string")
        if len(v) != 1:
            raise ValueError("tmq_code length must be 1")
        if not re.match(r"^[0-9A-Fa-f]$", v):
            raise ValueError("tmq_code must be a hex digit")
        return v.upper()

    @field_validator("lcapsec")
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
        bin4 = format(code_int, "04b")
        lcapsec_descriptions = {
            0: "无闰秒",
            1: "在记录中增加闰秒",
            2: "从记录中删除闰秒",
            3: "时钟源没有闰秒功能",
        }
        if code_int == 0:
            description = "正常运行，时钟锁定"
            precision = 0.0
            locked = True
        elif 1 <= code_int <= 0xB:
            exponent = code_int - 10
            precision = 10**exponent
            exponent_text = str(exponent) if exponent >= 0 else f"-{abs(exponent)}"
            description = f"时钟未锁定，误差 10^{exponent_text} s 以内"
            locked = False
        elif code_int == 0xF:
            description = "时钟错误，时间不可靠"
            precision = None
            locked = False
        else:
            description = "保留的时间质量码"
            precision = None
            locked = False
        return {
            "tmq_code": self.tmq_code,
            "binary": bin4,
            "value": code_int,
            "locked": locked,
            "precision_seconds": precision,
            "description": description,
            "lcapsec": self.lcapsec,
            "lcapsec_description": lcapsec_descriptions[self.lcapsec],
        }
