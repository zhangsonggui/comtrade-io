#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, Field

from comtrade_io.channel.analog import Analog
from comtrade_io.equipment.branch import ACCBranch, ACVBranch
from comtrade_io.type import TransWindLocation, WindFlag


class WindGroup(BaseModel):
    """
    绕组标识类

    表示变压器的绕组标识信息，用于标识不同的绕组及其相位关系。

    属性:
        wind_flag: 绕组标识符，如Y（星形）、D（三角形）等
        angle: 绕组角度，表示星形连接绕组的相角偏移
    """
    wind_flag: WindFlag = Field(default=WindFlag.Y, description="绕组接线方式")
    angle: int = Field(default=0, description="绕组角度")

    def __str__(self):
        """
        返回绕组标识符的字符串表示形式

        返回:
            格式化字符串，表示绕组标识符信息
        """
        return f"{self.wind_flag.value}{12 if self.angle == 0 else 11}"


class Igap(BaseModel):
    """
    中性点电流类

    表示变压器中性点的接地电流通道信息，用于记录中性点电流测量。

    实例化时可以传入通道索引和analog_channels字典，会自动解析为AnalogChannel对象。
    也可以直接传入AnalogChannel对象。

    属性:
        zgap: 中性点直接接地电流的通道
        zsgap: 中性点经间隙接地电流的通道
    """
    zgap: Optional[Analog] = Field(default=None, description="中性点直接接地电流的通道")
    zsgap: Optional[Analog] = Field(default=None, description="中性点经间隙接地电流的通道")

    def __str__(self):
        """
        返回中性点电流的XML字符串表示形式

        返回:
            格式化的XML字符串，表示中性点电流通道信息
        """
        zgap_idx = self.zgap.index if self.zgap else 0
        zsgap_idx = self.zsgap.index if self.zsgap else 0
        xml = f"<scl:Igap zGap_idx={zgap_idx} zSGap_idx={zsgap_idx} />"
        return xml


class TransformerWinding(BaseModel):
    """
    变压器绕组类

    表示变压器的单个绕组，包含绕组的电气参数和关联的电压电流通道。
    一个变压器可以有多个绕组（通常是高压绕组和低压绕组）。

    属性:
        bus_id: 母线索引号，表示该绕组连接的母线
        trans_wind_location: 绕组位置，标识绕组是高压侧还是低压侧
        reference: IEC61850参引，用于关联到IEC61850数据模型
        rated_voltage: 额定电压，单位通常为kV
        rated_current: 一次额定电流，单位通常为A
        bran_num: 分路数，表示绕组的分支数量
        wind_group: 绕组标识符，包含绕组类型和角度信息
        voltage: 交流电压通道，包含该绕组的电压通道索引
        currents: 交流电流通道列表，包含该绕组的电流分支信息
        igap: 中性点电流信息，包含接地电流的通道号
    """
    bus_id: int = Field(default=0, description="母线索引号")
    trans_wind_location: TransWindLocation = Field(default=TransWindLocation.HIGH, description="绕组位置")
    reference: Optional[str] = Field(default="", description="IEC61850参引")
    rated_voltage: float = Field(default=0.0, description="额定电压")
    rated_current: float = Field(default=0.0, description="一次额定电流")
    bran_num: int = Field(default=0, description="分路数")
    wind_group: WindGroup = Field(default_factory=WindGroup, description="绕组标识符")
    voltage: ACVBranch = Field(default_factory=ACVBranch, description="交流电压通道")
    currents: list[ACCBranch] = Field(default_factory=list, description="交流电流通道")
    igap: Igap = Field(default_factory=Igap, description="中性点电流通道号")

    def __str__(self):
        """
        返回变压器绕组的XML字符串表示形式

        返回:
            格式化的XML字符串，包含绕组及其所有子元素的完整表示
        """
        attrs = [
            f'location={self.trans_wind_location.value}"',
            f'srcRef={self.reference}"',
            f'VRtg={self.rated_voltage}"',
            f'ARtg={self.rated_current}"',
            f'bran_num={self.bran_num}"',
            f'bus_ID={self.bus_id}"',
            f'wG=""'
        ]
        attrs = [attr for attr in attrs if attr is not None]
        xml = f"<scl:TransformerWinding {' '.join(attrs)}>"
        xml += "\n\t\t\t" + str(self.voltage)
        for acc_bran in self.currents:
            xml += "\n\t\t\t" + str(acc_bran)
        xml += "\n\t\t\t" + str(self.igap)
        xml += "\n\t\t</scl:TransformerWinding>"
        return xml
