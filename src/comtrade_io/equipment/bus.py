#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import Field

from comtrade_io.equipment.branch import ACVBranch
from comtrade_io.equipment.equipment import Equipment
from comtrade_io.type import TvInstallSite


class Bus(Equipment):
    """母线部件模型"""
    rated_primary_voltage: float = Field(default=220.0, description="一次额定电压（kV）")
    rated_secondary_voltage: float = Field(default=100.0, description="二次额定电压（V）")
    tv_install_site: TvInstallSite = Field(default=TvInstallSite.BUS, description="电压互感器安装位置")
    voltage: ACVBranch = Field(default_factory=ACVBranch, description="电压通道")

    def to_dmf(self) -> str:
        """
        将母线部件对象转换为DMF格式XML字符串

        Returns:
            str: 转换后的DMF格式XML字符串
        """
        attrs = [
            f'idx="{self.index}"',
            f'bus_name="{self.name}"',
            f'srcRef="{self.reference}"',
            f'VRtg="{self.rated_primary_voltage}"',
            f'VRtgSnd="{self.rated_secondary_voltage}"',
            f'VRtgSnd_Pos="{self.tv_install_site.value}"',
            f'bus_uuid="{self.uuid}"'
        ]
        attrs = [attr for attr in attrs if attr is not None]
        xml = f"\t<scl:Bus {' '.join(attrs)}/>"
        xml += "\n\t\t" + str(self.voltage)
        xml += self._get_ana_chn_xml()
        xml += self._get_sta_chn_xml()
        xml += "\n\t</scl:Bus>"
        return xml

    def to_inf(self) -> str:
        """
        将母线部件对象转换为部件模型

        Returns:
            str: 转换后的部件模型字符串
        """
        tv_chn_str = ",".join(str(chn.index) for chn in self.acvs)
        attrs = [
            f"[PRIVATELY Bus_#{self.index}]",
            f"DEV_ID={self.name}",
            f"SYS_ID={self.uuid}",
            f"RATED_VALUE={self.rated_primary_voltage * 1000}V",
            f"TV_RATIO={self.rated_primary_voltage}kV/{self.rated_secondary_voltage}V",
            f"TV_CHNS={tv_chn_str}",
            f"TV_POS={self.tv_install_site.value}"
        ]
        return "\n".join(attrs)
