#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""将 Configure 对象转换为 EquipmentGroup 对象"""

from dataclasses import dataclass
from typing import Dict

from comtrade_io.model.channel import Analog, Status
from comtrade_io.model.configure import Configure
from comtrade_io.model.equipment import Bus, EquipmentGroup, Line, Transformer
from comtrade_io.model.equipment.branch import ACCBranch, ACVBranch
from comtrade_io.model.equipment.transformer_winding import TransformerWinding
from comtrade_io.model.type import (
    AnalogChannelFlag,
    AnalogChannelType,
    Phase,
    TransWindLocation,
    Unit,
)
from comtrade_io.utils import get_logger
from comtrade_io.utils.recognition.channel_recognizer import (
    ChannelRecognitionResult,
    RecognitionResult,
    recognize_analog_channel,
    recognize_status_channel,
)

logger = get_logger()

_TRANSFORMER_KEYWORDS = ("变", "主变", "变压器")
_WINDING_KEYWORDS = {
    "高压侧": TransWindLocation.HIGH,
    "中压侧": TransWindLocation.MEDIUM,
    "低压侧": TransWindLocation.LOW,
}
_PHASES_ABC = {Phase.PHASE_A, Phase.PHASE_B, Phase.PHASE_C}
_VOLTAGE_UNITS = {Unit.V, Unit.kV, Unit.mV}
_CURRENT_UNITS = {Unit.A, Unit.kA, Unit.mA}


@dataclass(frozen=True)
class _RecognizedStatus:
    channel: Status
    recognition: ChannelRecognitionResult
    equip: str


@dataclass(frozen=True)
class _RecognizedAnalog:
    channel: Analog
    recognition: ChannelRecognitionResult
    equip: str
    winding: TransWindLocation | None


def _is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def _channel_equip(
    channel: Analog | Status, result: ChannelRecognitionResult
) -> str | None:
    if _is_blank(channel.equip) and result.monitor:
        channel.equip = result.monitor
    return channel.equip.strip() if channel.equip else None


def _recognize_statuses(statuses: dict[int, Status]) -> list[_RecognizedStatus]:
    recognized: list[_RecognizedStatus] = []
    for st in statuses.values():
        result = recognize_status_channel(st.name or "")
        if result.result == RecognitionResult.UNUSED:
            continue

        equip = _channel_equip(st, result)
        if st.type is None:
            st.type = result.channel_type
        if st.flag is None:
            st.flag = result.channel_flag
        if not equip:
            continue
        recognized.append(_RecognizedStatus(st, result, equip))
    return recognized


def _recognize_analogs(analogs: dict[int, Analog]) -> list[_RecognizedAnalog]:
    recognized: list[_RecognizedAnalog] = []
    for ch in analogs.values():
        result = recognize_analog_channel(ch.name or "")
        if result.result == RecognitionResult.UNUSED:
            continue

        equip = _channel_equip(ch, result)
        if ch.type is None:
            ch.type = result.channel_type
        if ch.flag is None:
            ch.flag = result.channel_flag
        if not equip:
            continue
        recognized.append(
            _RecognizedAnalog(ch, result, equip, _detect_winding(ch.name or ""))
        )
    return recognized


def _detect_winding(channel_name: str) -> TransWindLocation | None:
    for keyword, location in _WINDING_KEYWORDS.items():
        if keyword in channel_name:
            return location
    return None


def _is_transformer_equip(equip: str) -> bool:
    return any(keyword in equip for keyword in _TRANSFORMER_KEYWORDS)


def _base_transformer_equip(equip: str) -> str:
    for keyword in _WINDING_KEYWORDS:
        idx = equip.find(keyword)
        if idx >= 0:
            return equip[:idx].rstrip("_ ")
    return equip


def _unit_matches(channel: Analog, expected_units: set[Unit]) -> bool:
    return channel.unit == Unit.NONE or channel.unit in expected_units


def _is_ac_voltage(item: _RecognizedAnalog) -> bool:
    ch = item.channel
    flag = item.recognition.channel_flag
    ch_flag = ch.flag
    is_voltage = flag == AnalogChannelFlag.TV or ch_flag == AnalogChannelFlag.TV
    return (
        item.recognition.channel_type == AnalogChannelType.A
        and is_voltage
        and _unit_matches(ch, _VOLTAGE_UNITS)
    )


def _is_ac_current(item: _RecognizedAnalog) -> bool:
    ch = item.channel
    flag = item.recognition.channel_flag
    ch_flag = ch.flag
    is_current = flag == AnalogChannelFlag.TA or ch_flag == AnalogChannelFlag.TA
    return (
        item.recognition.channel_type == AnalogChannelType.A
        and is_current
        and _unit_matches(ch, _CURRENT_UNITS)
    )


def _phase_set(items: list[_RecognizedAnalog]) -> set[Phase]:
    return {item.channel.phase for item in items if item.channel.phase is not None}


def _has_abc(items: list[_RecognizedAnalog]) -> bool:
    return _PHASES_ABC.issubset(_phase_set(items))


def _sort_channels(items: list[_RecognizedAnalog]) -> list[Analog]:
    return [item.channel for item in sorted(items, key=lambda item: item.channel.index)]


def _a_phase_channel(items: list[_RecognizedAnalog]) -> Analog:
    for item in sorted(items, key=lambda item: item.channel.index):
        if item.channel.phase == Phase.PHASE_A:
            return item.channel
    return sorted(items, key=lambda item: item.channel.index)[0].channel


def _group_voltage_channels(
    analogs: list[_RecognizedAnalog],
) -> dict[tuple[str, int | None], list[_RecognizedAnalog]]:
    groups: dict[tuple[str, int | None], list[_RecognizedAnalog]] = {}
    for item in analogs:
        if not _is_ac_voltage(item):
            continue
        key = (item.equip, item.recognition.voltage_level)
        groups.setdefault(key, []).append(item)
    return groups


def _group_current_channels(
    analogs: list[_RecognizedAnalog],
) -> dict[tuple[str, int | None], list[_RecognizedAnalog]]:
    groups: dict[tuple[str, int | None], list[_RecognizedAnalog]] = {}
    for item in analogs:
        if not _is_ac_current(item):
            continue
        key = (item.equip, item.recognition.voltage_level)
        groups.setdefault(key, []).append(item)
    return groups


def _matching_statuses(
    statuses: list[_RecognizedStatus], equip: str, voltage_level: int | None = None
) -> list[Status]:
    matched: list[Status] = []
    for item in statuses:
        if item.equip != equip:
            continue
        if (
            voltage_level is not None
            and item.recognition.voltage_level is not None
            and item.recognition.voltage_level != voltage_level
        ):
            continue
        matched.append(item.channel)
    return matched


def _find_bus(buses: list[Bus], voltage_level: int | None) -> Bus | None:
    if voltage_level is None:
        return None
    voltage_kv = voltage_level / 1000
    for bus in buses:
        if bus.rated_primary_voltage == voltage_kv:
            return bus
    return None


class CfgToEquipment:
    """将 Configure 对象转换为 EquipmentGroup 对象"""

    @staticmethod
    def convert(config: Configure) -> EquipmentGroup:
        recognized_statuses = _recognize_statuses(config.statuses)
        recognized_analogs = _recognize_analogs(config.analogs)

        voltage_groups = _group_voltage_channels(recognized_analogs)
        current_groups = _group_current_channels(recognized_analogs)

        buses = CfgToEquipment._build_buses(voltage_groups, recognized_statuses)
        transformers = CfgToEquipment._build_transformers(
            current_groups, voltage_groups, recognized_statuses, buses
        )
        lines = CfgToEquipment._build_lines(current_groups, recognized_statuses, buses)

        logger.info(
            f"CfgToEquipment转换完成: {len(buses)}个母线, "
            f"{len(lines)}条线路, {len(transformers)}个变压器"
        )

        return EquipmentGroup(
            description=config.description,
            analogs=config.analogs,
            statuses=config.statuses,
            buses=buses or None,
            lines=lines or None,
            transformers=transformers or None,
        )

    @staticmethod
    def _build_buses(
        voltage_groups: dict[tuple[str, int | None], list[_RecognizedAnalog]],
        statuses: list[_RecognizedStatus],
    ) -> list[Bus]:
        buses: list[Bus] = []
        for (equip, voltage_level), items in sorted(
            voltage_groups.items(),
            key=lambda item: min(i.channel.index for i in item[1]),
        ):
            if not _has_abc(items):
                continue
            analogs = _sort_channels(items)
            a_phase = _a_phase_channel(items)
            bus = Bus(
                index=len(buses) + 1,
                name=equip,
                rated_primary_voltage=a_phase.primary,
                rated_secondary_voltage=a_phase.secondary,
                voltage=ACVBranch.from_analog_channels(analogs),
                acvs=analogs,
                anas=analogs,
                stas=_matching_statuses(statuses, equip, voltage_level),
            )
            buses.append(bus)
        return buses

    @staticmethod
    def _build_lines(
        current_groups: dict[tuple[str, int | None], list[_RecognizedAnalog]],
        statuses: list[_RecognizedStatus],
        buses: list[Bus],
    ) -> list[Line]:
        lines: list[Line] = []
        for (equip, voltage_level), items in sorted(
            current_groups.items(),
            key=lambda item: min(i.channel.index for i in item[1]),
        ):
            if _is_transformer_equip(equip) or not _has_abc(items):
                continue
            analogs = _sort_channels(items)
            a_phase = _a_phase_channel(items)
            bus = _find_bus(buses, voltage_level)
            line = Line(
                index=len(lines) + 1,
                name=equip,
                bus_index=bus.index if bus else 0,
                rated_primary_voltage=(voltage_level / 1000) if voltage_level else 0.0,
                rated_primary_current=a_phase.primary,
                rated_secondary_current=a_phase.secondary,
                currents=ACCBranch.from_analog_channels(analogs),
                buses=[bus] if bus else [],
                accs=analogs,
                anas=analogs,
                stas=_matching_statuses(statuses, equip, voltage_level),
            )
            lines.append(line)
        return lines

    @staticmethod
    def _build_transformers(
        current_groups: dict[tuple[str, int | None], list[_RecognizedAnalog]],
        voltage_groups: dict[tuple[str, int | None], list[_RecognizedAnalog]],
        statuses: list[_RecognizedStatus],
        buses: list[Bus],
    ) -> list[Transformer]:
        # Build voltage index by equip (not by equip+voltage_level),
        # since transformer current channels often lack "kV" in source names.
        voltage_by_equip: dict[str, list[_RecognizedAnalog]] = {}
        for (vequip, _), items in voltage_groups.items():
            voltage_by_equip.setdefault(vequip, []).extend(items)

        transformer_groups: Dict[
            str, dict[TransWindLocation, list[_RecognizedAnalog]]
        ] = {}
        for (equip, _), items in current_groups.items():
            if not _is_transformer_equip(equip):
                continue
            base_equip = _base_transformer_equip(equip)
            for item in items:
                winding = item.winding or TransWindLocation.HIGH
                transformer_groups.setdefault(base_equip, {}).setdefault(
                    winding, []
                ).append(item)

        transformers: list[Transformer] = []
        for equip, winding_groups in sorted(
            transformer_groups.items(),
            key=lambda item: min(
                analog.channel.index for group in item[1].values() for analog in group
            ),
        ):
            valid_groups = {
                winding: items
                for winding, items in winding_groups.items()
                if _has_abc(items)
            }
            if not valid_groups:
                continue

            tr = Transformer(index=len(transformers) + 1, name=equip)
            tr_statuses = _matching_statuses(statuses, equip)
            if not tr_statuses:
                tr_statuses = [
                    item.channel
                    for item in statuses
                    if item.equip.startswith(equip) or equip.startswith(item.equip)
                ]
            tr.stas = tr_statuses

            for winding in (
                TransWindLocation.HIGH,
                TransWindLocation.MEDIUM,
                TransWindLocation.LOW,
            ):
                if winding not in valid_groups:
                    continue
                cur_items = valid_groups[winding]
                analogs = _sort_channels(cur_items)
                a_phase = _a_phase_channel(cur_items)
                voltage_level = cur_items[0].recognition.voltage_level
                bus = _find_bus(buses, voltage_level)
                all_vol_items = voltage_by_equip.get(cur_items[0].equip, [])
                vol_items = [
                    v
                    for v in all_vol_items
                    if (v.winding or TransWindLocation.HIGH) == winding
                ]
                winding_model = TransformerWinding(
                    bus_id=bus.index if bus else 0,
                    trans_wind_location=winding,
                    rated_voltage=(voltage_level / 1000) if voltage_level else 0.0,
                    rated_current=a_phase.primary,
                    voltage=ACVBranch.from_analog_channels(_sort_channels(vol_items)),
                    currents=ACCBranch.from_analog_channels(analogs),
                )
                tr.trans_winds.append(winding_model)

            if not tr.trans_winds:
                continue
            tr.winding_num = len(tr.trans_winds)
            tr.accs = [
                item.channel for items in valid_groups.values() for item in items
            ]
            tr.anas = list(tr.accs)
            tr.acvs = [
                item.channel
                for (_, _), items in voltage_groups.items()
                for item in items
                if _base_transformer_equip(item.equip) == equip
            ]
            transformers.append(tr)
        return transformers
