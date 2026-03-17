#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
线路参数模块

定义线路电气参数类，用于表示电力线路的阻抗、电容和互感参数。
包括RX（阻抗参数）、CG（电容参数）和MR（互感参数）三个类。
"""
from pydantic import BaseModel, Field


class RX(BaseModel):
    """
    线路阻抗参数类
    
    表示电力线路的电阻和电抗参数，包括正序和零序参数。
    这些参数用于电力系统稳态和暂态分析计算。
    
    属性:
        r1: 正序电阻，单位通常为Ω/km
        x1: 正序电抗，单位通常为Ω/km
        r0: 零序电阻，单位通常为Ω/km
        x0: 零序电抗，单位通常为Ω/km
    """
    r1: float = Field(default=0.0, description="正序电阻")
    x1: float = Field(default=0.0, description="正序电抗")
    r0: float = Field(default=0.0, description="零序电阻")
    x0: float = Field(default=0.0, description="零序电抗")

    def __str__(self):
        """
        返回线路阻抗参数的XML字符串表示形式
        
        返回:
            格式化的XML字符串，表示阻抗参数的所有属性
        """
        attrs = [
            f'r1="{self.r1}"',
            f'x1="{self.x1}"',
            f'r0="{self.r0}"',
            f'x0="{self.x0}"',
        ]

        return f'<scl:RX {" ".join(attrs)}/>'


class CG(BaseModel):
    """
    线路电容参数类
    
    表示电力线路的电容和电导参数，包括正序和零序参数。
    这些参数用于电力系统潮流计算和暂态分析。
    
    属性:
        c1: 正序电容，单位通常为μS/km
        c0: 零序电容，单位通常为μS/km
        g1: 正序电导，单位通常为μS/km
        g0: 零序电导，单位通常为μS/km
    """
    c1: float = Field(default=0.0, description="正序电容")
    c0: float = Field(default=0.0, description="零序电容")
    g1: float = Field(default=0.0, description="正序电导")
    g0: float = Field(default=0.0, description="零序电导")

    def __str__(self):
        """
        返回线路电容参数的XML字符串表示形式
        
        返回:
            格式化的XML字符串，表示电容参数的所有属性
        """
        attrs = [
            f'c1="{self.c1}"',
            f'c0="{self.c0}"',
            f'g1="{self.g1}"',
            f'g0="{self.g0}"',
        ]
        return f'<scl:CG {" ".join(attrs)}/>'


class MR(BaseModel):
    """
    线路互感参数类
    
    表示线路之间的互感参数，主要用于零序网络的计算。
    当两条平行线路之间存在电磁耦合时使用。
    
    属性:
        idx: 母线索引号，标识互感关联的母线
        mr0: 零序互感电阻，单位通常为Ω/km
        mx0: 零序互感电抗，单位通常为Ω/km
    """
    idx: int = Field(default=0, description="母线索引号")
    mr0: float = Field(default=0.0, description="零序互感电阻")
    mx0: float = Field(default=0.0, description="零序互感电抗")

    def __str__(self):
        """
        返回线路互感参数的XML字符串表示形式
        
        返回:
            格式化的XML字符串，表示互感参数的所有属性
        """
        attrs = [
            f'idx="{self.idx}"',
            f'mr0="{self.mr0}"',
            f'mx0="{self.mx0}"',
        ]
        return f'<scl:MR {" ".join(attrs)}/>'
