#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.model.channel import Analog, Status
from comtrade_io.model.description import Description
from comtrade_io.model.equipment import Bus, EquipmentGroup, Line, Transformer
from comtrade_io.model.equipment.branch import ACVBranch
from comtrade_io.parser.inf.analog_section import AnalogSection
from comtrade_io.parser.inf.bus_section import BusSection
from comtrade_io.parser.inf.configure_builder import (
    _apply_channel_parameters_internal,
)
from comtrade_io.parser.inf.description_section import DescriptionSection
from comtrade_io.parser.inf.line_section import LineSection
from comtrade_io.parser.inf.status_section import StatusSection
from comtrade_io.parser.inf.text_splitter import SectionData
from comtrade_io.parser.inf.transformer_section import TransformerSection
from comtrade_io.utils import get_logger

logger = get_logger()


def _get_voltage_from_channel(
    channels: list[Analog], buses: list[Bus]
) -> tuple[int, list[Bus]]:
    """根据通道列表找到对应的母线

    遍历通道，在母线列表中查找该通道所属的母线。
    若恰好匹配一条母线则返回其 index，否则返回 0。

    参数:
        channels: 电压通道列表（设备的 acvs）
        buses: 从 INF 解析出的全部母线列表

    返回:
        tuple: (bus_index, matched_buses)
            - bus_index: 匹配到的母线 index，未匹配或匹配多条时返回 0
            - matched_buses: 匹配到的母线对象列表
    """
    matched_buses = []
    for channel in channels:
        for bus in buses:
            voltage_ids = [chn.index for chn in bus.acvs]
            if channel.index in voltage_ids:
                if bus not in matched_buses:
                    matched_buses.append(bus)
                break
    bus_id = matched_buses[0].index if len(matched_buses) == 1 else 0
    return bus_id, matched_buses


def build_equipment_group(sections: SectionData) -> EquipmentGroup:
    """从节数据构建 EquipmentGroup 对象

    处理顺序：
    1. 构建模拟通道和开关量通道字典
    2. 应用参数段数据更新通道
    3. 构建母线、线路、变压器设备（依赖通道数据解析引用关系）
    4. 为线路匹配所属母线

    参数:
        sections: 由 split_sections() 返回的节数据

    返回:
        EquipmentGroup: 包含所有通道和设备信息的模型对象
    """
    analog_channels: dict[int, Analog] = {}
    for ch_data in sections.analog_channels:
        ch = AnalogSection.from_dict(ch_data)
        analog_channels[ch.index] = ch

    status_channels: dict[int, Status] = {}
    for ch_data in sections.status_channels:
        ch = StatusSection.from_dict(ch_data)
        status_channels[ch.index] = ch

    _apply_channel_parameters_internal(sections, analog_channels, status_channels)

    file_description = None
    if sections.file_description:
        file_description = DescriptionSection.from_dict(sections.file_description)

    buses: list[Bus] = []
    for bus_data in sections.buses:
        bus = BusSection.from_dict(bus_data, analog_channels, status_channels)
        bus.voltage = ACVBranch.from_analog_channels(bus.acvs)
        buses.append(bus)

    lines: list[Line] = []
    for line_data in sections.lines:
        line = LineSection.from_dict(line_data, analog_channels, status_channels)
        lines.append(line)

    for line_obj in lines:
        line_obj.bus_index, line_obj.buses = _get_voltage_from_channel(
            line_obj.acvs, buses
        )

    transformers: list[Transformer] = []
    for tr_data in sections.transformers:
        tr = TransformerSection.from_dict(tr_data, analog_channels, status_channels)
        transformers.append(tr)

    logger.info(
        f"EquipmentGroup构建完成: {len(analog_channels)}个模拟通道, "
        f"{len(status_channels)}个开关量通道, "
        f"{len(buses)}个母线, {len(lines)}条线路, {len(transformers)}个变压器"
    )

    return EquipmentGroup(
        description=file_description or Description(),
        analogs=analog_channels,
        statuses=status_channels,
        buses=buses,
        lines=lines,
        transformers=transformers,
    )
