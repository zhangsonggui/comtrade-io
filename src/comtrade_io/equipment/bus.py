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

    def bus2element(self) -> str:
        pass

    def bus2section(self) -> str:
        """
        将母线部件对象转换为部件模型

        Returns:
            str: 转换后的部件模型字符串
        """
        tv_chn_str = ",".join(str(chn.index) for chn in self.anas)
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
