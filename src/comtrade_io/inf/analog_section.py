#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.channel.analog import Analog
from comtrade_io.type import Phase, TranSide, Unit


class AnalogSection(Analog):
    """模拟部件模型"""

    @staticmethod
    def from_dict(data: dict) -> 'Analog':
        index = data.get("index", None)
        name = data.get("Channel_ID", None)
        phase = Phase.from_value(data.get("Phase_ID", ""))
        reference = data.get("Monitored_Component", "")
        unit = Unit.from_value(data.get("Unit", ""))
        multiplier = data.get("Channel_Multiplier", 1)
        offset = data.get("Channel_Offset", 0)
        delay = data.get("Channel_Skew", 0)
        min_value = data.get("Range_Minimum_Limit_Value", 0)
        max_value = data.get("Range_Maximum_Limit_Value", 0)
        primary = data.get("Channel_Ratio_Primary", 1)
        secondary = data.get("Channel_Ratio_Secondary", 1)
        tran_side = TranSide.from_value(data.get("Data_Primary_Secondary", "S"))

        analog_obj = Analog(
                index=index,
                name=name,
                phase=phase,
                reference=reference,
                unit=unit,
                multiplier=multiplier,
                offset=offset,
                delay=delay,
                min_value=min_value,
                max_value=max_value,
                primary=primary,
                secondary=secondary,
                tran_side=tran_side
        )
        return analog_obj
