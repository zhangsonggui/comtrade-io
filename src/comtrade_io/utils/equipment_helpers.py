"""CfgToEquipment 与 EquipmentGroup 共用的设备模型校验/补全辅助函数"""

from dataclasses import dataclass

from .recognition.channel_recognizer import (
    ChannelRecognitionResult,
    RecognitionResult,
    recognize_analog_channel,
    recognize_status_channel,
)
from ..model.channel import Analog, Status
from ..model.equipment.branch import ACCBranch, ACVBranch
from ..model.equipment.bus import Bus
from ..model.type import (
    AnalogChannelFlag,
    AnalogChannelType,
    Phase,
    TransWindLocation,
    Unit,
)

_TRANSFORMER_KEYWORDS = ("变", "主变", "变压器")
_WINDING_KEYWORDS = {
    "高压侧": TransWindLocation.HIGH,
    "中压侧": TransWindLocation.MEDIUM,
    "低压侧": TransWindLocation.LOW,
    "公共绕组": TransWindLocation.COMMON,
}
_PHASES_ABC = {Phase.PHASE_A, Phase.PHASE_B, Phase.PHASE_C}
_VOLTAGE_UNITS = {Unit.V, Unit.kV, Unit.mV}
_CURRENT_UNITS = {Unit.A, Unit.kA, Unit.mA}

_IGNORED_EQUIPS = frozenset({"kV", "kA", "V", "A", "W", "Hz", "kW", "kWh", "MW", "0"})


@dataclass(frozen=True)
class RecognizedStatus:
    channel: Status
    recognition: ChannelRecognitionResult
    equip: str


@dataclass(frozen=True)
class RecognizedAnalog:
    channel: Analog
    recognition: ChannelRecognitionResult
    equip: str
    winding: TransWindLocation | None


def find_grounding_channels(
    analogs: dict[int, Analog], base_equip: str
) -> tuple[Analog | None, Analog | None]:
    zgap = None
    zsgap = None
    for ch in analogs.values():
        if not ch.name or base_equip not in ch.name:
            continue
        if "间隙" in ch.name:
            zsgap = ch
        elif "中性点" in ch.name:
            zgap = ch
    return zgap, zsgap


def is_blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def channel_equip(
    channel: Analog | Status, result: ChannelRecognitionResult
) -> str | None:
    if result.monitor:
        channel.equip = result.monitor
    equip = channel.equip.strip() if channel.equip else None
    if equip and equip in _IGNORED_EQUIPS:
        return None
    return equip


def recognize_statuses(statuses: dict[int, Status]) -> list[RecognizedStatus]:
    recognized: list[RecognizedStatus] = []
    for st in statuses.values():
        result = recognize_status_channel(st.name or "")
        if result.result == RecognitionResult.UNUSED:
            continue

        equip = channel_equip(st, result)
        if st.type is None:
            st.type = result.channel_type
        if st.flag is None:
            st.flag = result.channel_flag
        if not equip:
            continue
        recognized.append(RecognizedStatus(st, result, equip))
    return recognized


def recognize_analogs(analogs: dict[int, Analog]) -> list[RecognizedAnalog]:
    recognized: list[RecognizedAnalog] = []
    for ch in analogs.values():
        result = recognize_analog_channel(ch.name or "")
        if result.result == RecognitionResult.UNUSED:
            continue

        equip = channel_equip(ch, result)
        if ch.type is None:
            ch.type = result.channel_type
        if ch.flag is None:
            ch.flag = result.channel_flag
        if not equip:
            continue
        recognized.append(
            RecognizedAnalog(ch, result, equip, detect_winding(ch.name or ""))
        )
    return recognized


def detect_winding(channel_name: str) -> TransWindLocation | None:
    for keyword, location in _WINDING_KEYWORDS.items():
        if keyword in channel_name:
            return location
    return None


def is_transformer_equip(equip: str) -> bool:
    return any(keyword in equip for keyword in _TRANSFORMER_KEYWORDS)


def base_transformer_equip(equip: str) -> str:
    for keyword in _WINDING_KEYWORDS:
        idx = equip.find(keyword)
        if idx >= 0:
            return equip[:idx].rstrip("_ ")
    return equip


def unit_matches(channel: Analog, expected_units: set[Unit]) -> bool:
    return channel.unit == Unit.NONE or channel.unit in expected_units


def is_ac_voltage(item: RecognizedAnalog) -> bool:
    ch = item.channel
    flag = item.recognition.channel_flag
    ch_flag = ch.flag
    is_voltage = flag == AnalogChannelFlag.TV or ch_flag == AnalogChannelFlag.TV
    return (
        item.recognition.channel_type == AnalogChannelType.A
        and is_voltage
        and unit_matches(ch, _VOLTAGE_UNITS)
    )


def is_ac_current(item: RecognizedAnalog) -> bool:
    ch = item.channel
    flag = item.recognition.channel_flag
    ch_flag = ch.flag
    is_current = flag == AnalogChannelFlag.TA or ch_flag == AnalogChannelFlag.TA
    return (
        item.recognition.channel_type == AnalogChannelType.A
        and is_current
        and unit_matches(ch, _CURRENT_UNITS)
    )


def phase_set(items: list[RecognizedAnalog]) -> set[Phase]:
    return {item.channel.phase for item in items if item.channel.phase is not None}


def has_abc(items: list[RecognizedAnalog]) -> bool:
    return _PHASES_ABC.issubset(phase_set(items))


def sort_channels(items: list[RecognizedAnalog]) -> list[Analog]:
    return [item.channel for item in sorted(items, key=lambda item: item.channel.index)]


def a_phase_channel(items: list[RecognizedAnalog]) -> Analog:
    for item in sorted(items, key=lambda item: item.channel.index):
        if item.channel.phase == Phase.PHASE_A:
            return item.channel
    return sorted(items, key=lambda item: item.channel.index)[0].channel


def group_voltage_channels(
    analogs: list[RecognizedAnalog],
) -> dict[tuple[str, int | None], list[RecognizedAnalog]]:
    groups: dict[tuple[str, int | None], list[RecognizedAnalog]] = {}
    for item in analogs:
        if not is_ac_voltage(item):
            continue
        key = (item.equip, item.recognition.voltage_level)
        groups.setdefault(key, []).append(item)
    return groups


def group_current_channels(
    analogs: list[RecognizedAnalog],
) -> dict[tuple[str, int | None], list[RecognizedAnalog]]:
    groups: dict[tuple[str, int | None], list[RecognizedAnalog]] = {}
    for item in analogs:
        if not is_ac_current(item):
            continue
        key = (item.equip, item.recognition.voltage_level)
        groups.setdefault(key, []).append(item)
    return groups


def matching_statuses(
    statuses: list[RecognizedStatus], equip: str, voltage_level: int | None = None
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


def find_bus(buses: list[Bus], voltage_level: int | None) -> Bus | None:
    if voltage_level is None:
        return None
    voltage_kv = voltage_level / 1000
    for bus in buses:
        if bus.rated_primary_voltage == voltage_kv:
            return bus
    return None


def find_buses(buses: list[Bus], equip: str, voltage_level: int | None) -> list[Bus]:
    matched: list[Bus] = []
    for bus in buses:
        if bus.name == equip:
            matched.append(bus)
    if not matched and voltage_level is not None:
        voltage_kv = voltage_level / 1000
        for bus in buses:
            if bus.rated_primary_voltage == voltage_kv:
                matched.append(bus)
                if len(matched) >= 2:
                    break
    return matched[:2]


def winding_voltage_contained(
    vol_items: list[RecognizedAnalog], bus: Bus | None
) -> bool:
    if bus is None or not bus.acvs:
        return False
    bus_indices = {a.index for a in bus.acvs}
    return all(v.channel.index in bus_indices for v in vol_items)


def get_or_create_supplement_bus(
    supplement_buses: dict[tuple[str, TransWindLocation, int | None], Bus],
    buses: list[Bus],
    base_equip: str,
    winding: TransWindLocation,
    voltage_level: int | None,
    vol_items: list[RecognizedAnalog],
    statuses: list[RecognizedStatus],
) -> Bus | None:
    if not vol_items:
        return None
    key = (base_equip, winding, voltage_level)
    bus = supplement_buses.get(key)
    if bus is not None:
        existing = {a.index for a in bus.acvs}
        new_items = [v for v in vol_items if v.channel.index not in existing]
        if new_items:
            merged = list(bus.acvs) + [v.channel for v in new_items]
            merged.sort(key=lambda a: a.index)
            bus.acvs = merged
            bus.anas = list(merged)
            bus.voltage = ACVBranch.from_analog_channels(merged)
        return bus

    analogs = sort_channels(vol_items)
    a_phase = a_phase_channel(vol_items)
    bus = Bus(
        index=len(buses) + 1,
        name=f"{base_equip}{winding.description}电压",
        rated_primary_voltage=a_phase.primary / a_phase.secondary / 10 if a_phase.secondary else 0.0,
        rated_secondary_voltage=a_phase.secondary,
        voltage=ACVBranch.from_analog_channels(analogs),
        acvs=analogs,
        anas=analogs,
        stas=matching_statuses(statuses, base_equip, voltage_level),
    )
    buses.append(bus)
    supplement_buses[key] = bus
    return bus


def acc_branch_channels(branch: ACCBranch) -> list[Analog]:
    return [c for c in (branch.ia, branch.ib, branch.ic, branch.i0) if c is not None]


def acv_branch_channels(branch: ACVBranch) -> list[Analog]:
    return [c for c in (branch.ua, branch.ub, branch.uc, branch.un, branch.ul) if c is not None]


def dedup_channels_by_index(channels: list[Analog]) -> list[Analog]:
    seen: set[int] = set()
    result: list[Analog] = []
    for ch in channels:
        if ch is None or ch.index in seen:
            continue
        seen.add(ch.index)
        result.append(ch)
    return sorted(result, key=lambda a: a.index)


def collect_line_channels(line) -> tuple[list[Analog], list[Analog]]:
    accs: list[Analog] = []
    for branch in (line.currents or []):
        accs.extend(acc_branch_channels(branch))
    accs.extend(line.accs or [])
    acvs: list[Analog] = []
    for bus in (line.buses or []):
        if bus.voltage is not None:
            acvs.extend(acv_branch_channels(bus.voltage))
    acvs.extend(line.acvs or [])
    return dedup_channels_by_index(accs), dedup_channels_by_index(acvs)


def collect_transformer_channels(transformer) -> tuple[list[Analog], list[Analog]]:
    accs: list[Analog] = []
    acvs: list[Analog] = []
    for tw in (transformer.trans_winds or []):
        for branch in (tw.currents or []):
            accs.extend(acc_branch_channels(branch))
        if tw.voltage is not None:
            acvs.extend(acv_branch_channels(tw.voltage))
    accs.extend(transformer.accs or [])
    acvs.extend(transformer.acvs or [])
    return dedup_channels_by_index(accs), dedup_channels_by_index(acvs)

