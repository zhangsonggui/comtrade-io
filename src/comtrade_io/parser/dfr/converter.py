#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WNDR → COMTRADE CFG 转换器。"""

from datetime import datetime

from comtrade_io.model.channel.analog import Analog
from comtrade_io.model.channel.status import Status
from comtrade_io.model.configure import Configure
from comtrade_io.model.description import (
    ChannelNum,
    Description,
    Header,
    Sampling,
    Segment,
)
from comtrade_io.model.type import DataType, Phase, TranSide, Unit, Version
from comtrade_io.parser.dfr.wndr_section import WndrSection
from comtrade_io.utils import get_logger

logger = get_logger()


def _unit_from_ch_type(ch_type: int) -> Unit:
    if ch_type <= 10:
        return Unit.A
    elif ch_type == 100:
        return Unit.kV
    return Unit.NONE


def _secondary_from_ch_type(ch_type: int) -> float:
    if ch_type > 0:
        return float(ch_type)
    return 1.0


def _scale_primary(primary: float, ch_type: int, unit: Unit) -> float:
    if primary == 0.0:
        return 1.0
    if unit == Unit.kV and primary > 10000:
        return primary / 1000.0
    return primary


def _translate_phase(phase_code: str) -> str:
    mapping = {
        "а": "A",
        "в": "B",
        "с": "C",
        "А": "A",
        "В": "B",
        "С": "C",
    }
    return mapping.get(phase_code, phase_code)


def wndr_to_configure(
    wndr: WndrSection, file_mtime: datetime | None = None
) -> Configure:
    station_name = wndr.station_name
    recorder = f"{station_name}_DFR"

    header = Header(
        station=station_name,
        recorder=recorder,
        version=Version.V1999,
    )

    channel_num = ChannelNum(
        total=wndr.analog_count + wndr.status_count,
        analog=wndr.analog_count,
        status=wndr.status_count,
    )

    analogs: dict[int, Analog] = {}
    for ch in wndr.analog_channels:
        unit = _unit_from_ch_type(ch.ch_type)
        secondary = _secondary_from_ch_type(ch.ch_type)

        phase_str = _translate_phase(ch.phase)
        if not phase_str:
            phase_str = ""

        primary = _scale_primary(ch.rated_primary, ch.ch_type, unit)

        analogs[ch.idx] = Analog(
            index=ch.idx,
            name=ch.name,
            phase=Phase.from_value(phase_str, Phase.NONE),
            equip=ch.circuit,
            unit=unit,
            multiplier=ch.conv_factor,
            offset=0.0,
            delay=0.0,
            min_value=-32768.0,
            max_value=32767.0,
            primary=primary,
            secondary=secondary,
            tran_side=TranSide.S,
        )

    statuses: dict[int, Status] = {}
    for seq, ch in enumerate(wndr.status_channels, 1):
        statuses[seq] = Status(
            index=seq,
            name=ch.name,
        )

    sampling_rate = wndr.samples_per_cycle * int(wndr.grid_freq)
    end_point = wndr.total_samples if wndr.total_samples > 0 else 12612
    segment = Segment(samp=sampling_rate, end_point=end_point)

    sampling = Sampling(
        freq=wndr.grid_freq,
        segments=[segment],
    )

    if file_mtime:
        file_start_time = file_mtime
        trigger_time = file_mtime
    else:
        now = datetime.now()
        file_start_time = now
        trigger_time = now

    description = Description(
        header=header,
        channel_num=channel_num,
        sampling=sampling,
        file_start_time=file_start_time,
        trigger_time=trigger_time,
        data_type=DataType.BINARY,
        timemult=1.0,
    )

    return Configure(
        description=description,
        analogs=analogs,
        statuses=statuses,
    )
