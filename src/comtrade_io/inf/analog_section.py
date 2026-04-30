#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.channel.analog import Analog
from comtrade_io.type import AnalogChannelFlag, Phase, TranSide, Unit


class AnalogSection(Analog):
    """模拟部件模型"""

    @staticmethod
    def from_dict(data: dict) -> 'Analog':
        index = data.get("index", None)
        name = data.get("Channel_ID") or data.get("name")
        phase = Phase.from_value(data.get("Phase_ID", "") or data.get("phase", ""))
        reference = data.get("Monitored_Component") or data.get("reference", "")
        unit = Unit.from_value(data.get("Unit", "") or data.get("Channel_Units", "") or data.get("unit", ""))

        def to_float(val, default):
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        multiplier = to_float(data.get("Channel_Multiplier"), 1.0)
        offset = to_float(data.get("Channel_Offset"), 0.0)
        delay = to_float(data.get("Channel_Skew"), 0.0)
        min_value = to_float(data.get("Range_Minimum_Limit_Value"), 0.0)
        max_value = to_float(data.get("Range_Maximum_Limit_Value"), 0.0)
        primary = to_float(data.get("Channel_Ratio_Primary"), 1.0)
        secondary = to_float(data.get("Channel_Ratio_Secondary"), 1.0)
        tran_side = TranSide.from_value(data.get("Data_Primary_Secondary", "S"))
        freq = to_float(data.get("freq"), 50.0)

        # 参数段字段映射：t1→primary, t2→secondary, ad→au, bd→bu
        if "t1" in data:
            primary = to_float(data["t1"], 1.0)
        if "t2" in data:
            secondary = to_float(data["t2"], 1.0)
        analog_au = to_float(data["ad"], None) if "ad" in data else None
        analog_bu = to_float(data["bd"], None) if "bd" in data else None

        idx_org = data.get("idx_org")
        if idx_org is not None:
            idx_org = int(idx_org) if isinstance(idx_org, str) else idx_org

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
                tran_side=tran_side,
                freq=freq,
                au=analog_au,
                bu=analog_bu,
        )

        if idx_org is not None:
            analog_obj.idx_org = idx_org

        # 参数段中的 type 实际上是 flag 名称（TV/TA/DV/DA 等）
        type_val = data.get("type")
        if type_val:
            try:
                flag = AnalogChannelFlag.from_name(type_val)
                analog_obj.flag = flag
                analog_obj.type = flag.type if flag.type else None
            except ValueError:
                pass

        return analog_obj
