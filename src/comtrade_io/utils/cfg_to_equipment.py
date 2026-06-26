"""将 Configure 对象转换为 EquipmentGroup 对象"""

from typing import Dict

from . import get_logger
from .equipment_helpers import (
    RecognizedAnalog,
    RecognizedStatus,
    a_phase_channel,
    base_transformer_equip,
    find_bus,
    find_buses,
    find_grounding_channels,
    get_or_create_supplement_bus,
    group_current_channels,
    group_voltage_channels,
    has_abc,
    is_transformer_equip,
    matching_statuses,
    recognize_analogs,
    recognize_statuses,
    sort_channels,
    winding_voltage_contained,
)
from ..model.channel import Analog
from ..model.configure import Configure
from ..model.equipment import Bus, EquipmentGroup, Line, Transformer
from ..model.equipment.branch import ACCBranch, ACVBranch
from ..model.equipment.transformer_winding import Igap, TransformerWinding
from ..model.type import TransWindLocation

logger = get_logger()


class CfgToEquipment:
    """将 Configure 对象转换为 EquipmentGroup 对象"""

    @staticmethod
    def convert(config: Configure) -> EquipmentGroup:
        recognized_statuses = recognize_statuses(config.statuses)
        recognized_analogs = recognize_analogs(config.analogs)

        voltage_groups = group_voltage_channels(recognized_analogs)
        current_groups = group_current_channels(recognized_analogs)

        buses = CfgToEquipment._build_buses(voltage_groups, recognized_statuses)
        transformers = CfgToEquipment._build_transformers(
            current_groups, voltage_groups, recognized_statuses, buses, config.analogs
        )
        lines = CfgToEquipment._build_lines(current_groups, recognized_statuses, buses)

        logger.info(
            f"CfgToEquipment转换完成: {len(buses)}个母线, "
            f"{len(lines)}条线路, {len(transformers)}个变压器"
        )

        eg = EquipmentGroup(
            description=config.description,
            analogs=config.analogs,
            statuses=config.statuses,
            buses=buses or None,
            lines=lines or None,
            transformers=transformers or None,
        )
        eg.validate_and_supplement()
        return eg

    @staticmethod
    def _build_buses(
        voltage_groups: dict[tuple[str, int | None], list[RecognizedAnalog]],
        statuses: list[RecognizedStatus],
    ) -> list[Bus]:
        buses: list[Bus] = []
        for (equip, voltage_level), items in sorted(
            voltage_groups.items(),
            key=lambda item: min(i.channel.index for i in item[1]),
        ):
            if not has_abc(items):
                continue
            analogs = sort_channels(items)
            a_phase = a_phase_channel(items)
            bus = Bus(
                index=len(buses) + 1,
                name=equip,
                rated_primary_voltage=a_phase.primary / a_phase.secondary / 10 if a_phase.secondary else 0.0,
                rated_secondary_voltage=a_phase.secondary,
                voltage=ACVBranch.from_analog_channels(analogs),
                acvs=analogs,
                anas=analogs,
                stas=matching_statuses(statuses, equip, voltage_level),
            )
            buses.append(bus)
        return buses

    @staticmethod
    def _build_lines(
        current_groups: dict[tuple[str, int | None], list[RecognizedAnalog]],
        statuses: list[RecognizedStatus],
        buses: list[Bus],
    ) -> list[Line]:
        lines: list[Line] = []
        for (equip, voltage_level), items in sorted(
            current_groups.items(),
            key=lambda item: min(i.channel.index for i in item[1]),
        ):
            if is_transformer_equip(equip) or not has_abc(items):
                continue
            analogs = sort_channels(items)
            a_phase = a_phase_channel(items)
            matched_buses = find_buses(buses, equip, voltage_level)
            line = Line(
                index=len(lines) + 1,
                name=equip,
                bus_index=matched_buses[0].index if matched_buses else 0,
                rated_primary_voltage=(voltage_level / 1000) if voltage_level else 0.0,
                rated_primary_current=a_phase.primary,
                rated_secondary_current=a_phase.secondary,
                currents=ACCBranch.from_analog_channels(analogs),
                buses=matched_buses,
                accs=analogs,
                anas=analogs,
                stas=matching_statuses(statuses, equip, voltage_level),
            )
            lines.append(line)
        return lines

    @staticmethod
    def _build_transformers(
        current_groups: dict[tuple[str, int | None], list[RecognizedAnalog]],
        voltage_groups: dict[tuple[str, int | None], list[RecognizedAnalog]],
        statuses: list[RecognizedStatus],
        buses: list[Bus],
        all_analogs: dict[int, Analog],
    ) -> list[Transformer]:
        voltage_by_equip: dict[str, list[RecognizedAnalog]] = {}
        for (vequip, _), items in voltage_groups.items():
            voltage_by_equip.setdefault(vequip, []).extend(items)

        transformer_groups: Dict[
            str, dict[TransWindLocation, list[RecognizedAnalog]]
        ] = {}
        for (equip, _), items in current_groups.items():
            if not is_transformer_equip(equip):
                continue
            base_equip = base_transformer_equip(equip)
            for item in items:
                winding = item.winding or TransWindLocation.HIGH
                transformer_groups.setdefault(base_equip, {}).setdefault(
                    winding, []
                ).append(item)

        transformers: list[Transformer] = []
        supplement_buses: dict[
            tuple[str, TransWindLocation, int | None], Bus
        ] = {}
        for equip, winding_groups in sorted(
            transformer_groups.items(),
            key=lambda item: min(
                analog.channel.index for group in item[1].values() for analog in group
            ),
        ):
            valid_groups = {
                winding: items
                for winding, items in winding_groups.items()
                if has_abc(items)
            }
            if not valid_groups:
                continue

            tr = Transformer(index=len(transformers) + 1, name=equip)
            tr_statuses = matching_statuses(statuses, equip)
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
                TransWindLocation.COMMON,
            ):
                if winding not in valid_groups:
                    continue
                cur_items = valid_groups[winding]
                ch_list = sort_channels(cur_items)
                a_phase = a_phase_channel(cur_items)
                voltage_level = cur_items[0].recognition.voltage_level
                bus = find_bus(buses, voltage_level)
                all_vol_items = voltage_by_equip.get(cur_items[0].equip, [])
                vol_items = [
                    v
                    for v in all_vol_items
                    if (v.winding or TransWindLocation.HIGH) == winding
                ]
                if not winding_voltage_contained(vol_items, bus):
                    bus = get_or_create_supplement_bus(
                        supplement_buses,
                        buses,
                        equip,
                        winding,
                        voltage_level,
                        vol_items,
                        statuses,
                    )
                rated_voltage = bus.rated_primary_voltage if bus else ((voltage_level / 1000) if voltage_level else 0.0)
                zgap_ch, zsgap_ch = find_grounding_channels(all_analogs, equip)
                winding_model = TransformerWinding(
                    bus_id=bus.index if bus else 0,
                    trans_wind_location=winding,
                    rated_voltage=rated_voltage,
                    rated_current=a_phase.primary,
                    voltage=ACVBranch.from_analog_channels(sort_channels(vol_items)),
                    currents=ACCBranch.from_analog_channels(ch_list),
                    igap=Igap(zgap=zgap_ch, zsgap=zsgap_ch),
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
                if base_transformer_equip(item.equip) == equip
            ]
            transformers.append(tr)
        return transformers
