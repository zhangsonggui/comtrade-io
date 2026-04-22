#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pydantic import Field

from comtrade_io.equipment.equipment import Equipment
from comtrade_io.equipment.transformer_winding import TransformerWinding


class Transformer(Equipment):
    """
    变压器类

    表示电力系统中的变压器设备，包含额定功率和多个绕组。
    变压器是连接不同电压等级电网的关键设备。

    属性:
        capacity: 变压器额定功率，单位通常为MVA
        transWinds: 变压器绕组列表，包含该变压器的所有绕组
        transformer_uuid: 变压器唯一标识符
        anas: 模拟通道列表，继承自基类
        stas: 开关量通道列表，继承自基类
    """
    capacity: float = Field(default=0.0, description="变压器额定功率")
    winding_num: int = Field(default=3, description="绕组数量")
    trans_winds: list[TransformerWinding] = Field(default_factory=list, description="变压器绕组")

    def to_dmf(self):
        """
        返回变压器的XML字符串表示形式

        返回:
            格式化的XML字符串，包含变压器及其所有绕组的完整表示
        """
        attrs = [
            f'idx="{self.index}"',
            f'trm_name="{self.name}"',
            f'srcRef="{self.reference}"',
            f'pwrRtg="{self.capacity}"',
            f'transformer_uuid="{self.uuid}"'
        ]
        attrs = [attr for attr in attrs if attr is not None]
        xml = f"\t<scl:Transformer {' '.join(attrs)}>"

        for trans_wind in self.trans_winds:
            xml += "\n\t\t" + trans_wind.to_dmf()
        xml += self._get_ana_chn_xml()
        xml += self._get_sta_chn_xml()
        xml += "\n\t</scl:Transformer>"
        return xml

    def to_inf(self) -> str:
        """
        将变压器对象转换为部件模型

        Returns:
            str: 变压器部件模型字符串
        """
        attrs = [
            f"[PRIVATELY Transformer_#{self.index}]",
            f"DEV_ID={self.name}",
            f"SYS_ID={self.uuid}",
            f"CAPACITY={self.capacity}(MVA)",
            f"WINDING_NUM={len(self.trans_winds)}"
        ]
        for trans_wind in self.trans_winds:
            attrs.append(trans_wind.to_inf())
        return "\n".join(attrs)
