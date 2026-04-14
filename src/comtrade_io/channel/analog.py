#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import Field

from comtrade_io.base import ReferenceBaseModel
from comtrade_io.channel.channel import ChannelBaseModel
from comtrade_io.type import TranSide, Unit
from comtrade_io.utils import get_logger

logging = get_logger()


class Analog(ChannelBaseModel, ReferenceBaseModel):
    """模拟量通道类

    表示COMTRADE配置文件中的模拟量通道信息，包含通道的各种电气参数。

    属性:
        index: 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        name: 通道标识（ch_id）
        phase: 通道相别标识（ph）
        equip: 被监视的电路元件（ccbm）
        reference: IEC61850参考
        unit: 通道单位
        multiplier: 通道增益系数(实数,可使用标准浮点标记法)
        offset: 通道偏移量
        delay: 通道时滞（μs）
        min_value: 数值最小值
        max_value: 数值最大值
        primary: 互感器一次系数
        secondary: 互感器二次系数
        tran_side: 转换标识(P/S)
        primary_min_value: 通道一次侧量程的最小值，仅对直流类型有效
        primary_max_value: 通道一次侧量程的最大值，仅对直流类型有效
        secondary_min_value: 通道二次侧量程的最小值，仅对直流类型有效
        secondary_max_value: 通道二次侧量程的最大值，仅对直流类型有效
        freq: 模拟量频率
        au: 模拟量标幺
        bu: 模拟量标幺
        unit_multiplier: 模拟量增益系数
        data: 通道数据，一维数组
    """
    unit: Unit = Field(default=Unit.NONE, description="通道单位")
    multiplier: float = Field(default=1.0, ge=0.0, description="通道增益系数(实数,可使用标准浮点标记法)")
    offset: float = Field(default=0.0, description="通道偏移量")
    delay: float = Field(default=0.0, description="通道时滞（μs）")
    min_value: float = Field(default=0.0, description="数值最小值")
    max_value: float = Field(default=0.0, description="数值最大值")
    primary: float = Field(default=1.0, description="互感器一次系数")
    secondary: float = Field(default=1.0, description="互感器二次系数")
    tran_side: TranSide = Field(default=TranSide.S, description="转换标识(P/S)")
    primary_min_value: float = Field(default=0.0, description="通道一次侧量程的最小值，仅对直流类型有效")
    primary_max_value: float = Field(default=0.0, description="通道一次侧量程的最大值，仅对直流类型有效")
    secondary_min_value: float = Field(default=0.0, description="通道二次侧量程的最小值，仅对直流类型有效")
    secondary_max_value: float = Field(default=0.0, description="通道二次侧量程的最大值，仅对直流类型有效")
    freq: float = Field(default=50.0, description="模拟量频率")
    au: float = Field(default=1.0, description="模拟量标幺")
    bu: float = Field(default=0.0, description="模拟量标幺")
    unit_multiplier: str = Field(default="", description="模拟量增益系数")

    def __str__(self):
        """返回对象的字符串表示形式

        该方法扩展了父类的__str__方法，在其基础上添加了当前对象的特定属性信息，
        包括单位值、添加标志、偏移量、延迟、最小值、最大值、主次标识和传输侧等信息。

        返回:
            str: 包含父类字符串表示和当前对象所有属性信息的完整字符串
        """
        return (
                super().__str__()
                + f",{self.unit.value},{self.multiplier},{self.offset},{self.delay}"
                + f",{self.min_value},{self.max_value},{self.primary},{self.secondary}"
                + f",{self.tran_side.value}"
        )

    def to_dmf(self):
        """将模拟量通道对象转换为DMF格式字符串

        返回:
            str: 转换后的DMF格式字符串
        """
        attrs = [
            f'idx_cfg="{self.index}"',
            f'idx_org="{self.idx_org}"',
            f'type="{self.type.value}"',
            f'flag="{self.flag.value}"',
            f'freq="{self.freq}"',
            f'au="{self.au}"',
            f'bu="{self.bu}"',
            f'sIUnit="{self.unit.value}"',
            f'multiplier="{self.unit_multiplier}"',
            f'primary="{self.primary}"',
            f'secondary="{self.secondary}"',
            f'ps="{self.tran_side.value}"',
            f'idx_rl="0"',
            f'ph="{self.phase.value}"'
        ]

        return f'<scl:Analog {" ".join(attrs)} />'

    def to_inf(self) -> str:
        """将模拟量通道对象转换为模拟部件模型字符串

        返回:
            str: 转换后的INF格式字符串
        """
        attrs = [
            f"[Public Analog_Channel_#{self.index}]",
            f"Channel_ID={self.name}",
            f"Phase_ID={self.phase.value}",
            f"Monitored_Component={self.reference}",
            f"Channel_Units={self.unit.value}",
            f"Channel_Multiplier={self.multiplier}",
            f"Channel_Offset={self.offset}",
            f"Channel_Skew={self.delay}",
            f"Range_Minimum_Limit_Value={self.min_value}",
            f"Range_Maximum_Limit_Value={self.max_value}",
            f"Channel_Ratio_Primary={self.primary}",
            f"Channel_Ratio_Secondary={self.secondary}",
            f"Data_Primary_Secondary={self.tran_side.value}"
        ]
        return "\n".join(attrs)
