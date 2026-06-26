from pydantic import BaseModel, Field

from .bus import Bus
from .line import Line
from .transformer import Transformer
from ..channel import Analog, Status
from ..description import Description
from ..type import TransWindLocation
from ...utils import get_logger
from ...utils.equipment_helpers import (
    base_transformer_equip,
    collect_line_channels,
    collect_transformer_channels,
    dedup_channels_by_index,
    get_or_create_supplement_bus,
    group_voltage_channels,
    is_transformer_equip,
    recognize_analogs,
    recognize_statuses,
)

logger = get_logger()

class EquipmentGroup(BaseModel):
    description: Description = Field(default_factory=Description, description="描述文件")
    buses: list[Bus] | None = Field(default_factory=list, description="母线")
    lines: list[Line] | None = Field(default_factory=list, description="线路")
    transformers: list[Transformer] | None = Field(
        default_factory=list, description="变压器"
    )
    analogs: dict[int, Analog] | None = Field(
        default_factory=dict, description="模拟通道"
    )
    statuses: dict[int, Status] | None = Field(
        default_factory=dict, description="状态量通道"
    )

    def validate_and_supplement(
        self,
        analogs: dict[int, Analog] | None = None,
        statuses: dict[int, Status] | None = None,
    ) -> None:
        """校验并补全设备模型

        基于传入的 analogs/statuses 通道信息（默认取 self.analogs/self.statuses），
        检查 buses/lines/transformers 的完整性，对缺失的母线（当前仅主变绕组
        电压母线）进行补全。

        参数:
            analogs: 用于校验补全的模拟通道字典；为 None 时使用 self.analogs。
                     当 EquipmentGroup 由 DMF/INF 加载（通道 name 缺失）时，
                     应传入 CFG 来源的 analogs。
            statuses: 用于校验补全的状态通道字典；为 None 时使用 self.statuses。
        """
        self._supplement_transformer_voltage_buses(analogs, statuses)
        self._rebuild_channels_from_branches()
        self._validate_channels_consistency()

    def _supplement_transformer_voltage_buses(
        self,
        analogs: dict[int, Analog] | None,
        statuses: dict[int, Status] | None,
    ) -> None:
        source_analogs = analogs if analogs is not None else self.analogs
        if not source_analogs:
            return
        buses = self.buses if self.buses is not None else []
        if self.buses is None:
            self.buses = buses

        recognized = recognize_analogs(source_analogs)
        if not recognized:
            return
        voltage_groups = group_voltage_channels(recognized)
        if not voltage_groups:
            return

        source_statuses = statuses if statuses is not None else (self.statuses or {})
        existing_indices: set[int] = {
            a.index for bus in buses for a in (bus.acvs or [])
        }
        supplement_buses: dict[tuple[str, TransWindLocation, int | None], Bus] = {}

        for (equip, voltage_level), items in voltage_groups.items():
            if not is_transformer_equip(equip):
                continue
            base_equip = base_transformer_equip(equip)
            winding_items: dict[TransWindLocation, list] = {}
            for v in items:
                w = v.winding
                if w is None:
                    continue
                winding_items.setdefault(w, []).append(v)
            for winding, vol_items in winding_items.items():
                if all(v.channel.index in existing_indices for v in vol_items):
                    continue
                new_bus = get_or_create_supplement_bus(
                    supplement_buses,
                    buses,
                    base_equip,
                    winding,
                    voltage_level,
                    vol_items,
                    recognize_statuses(source_statuses),
                )
                if new_bus is not None:
                    existing_indices.update(a.index for a in (new_bus.acvs or []))

        self._sync_transformer_winding_bus_id(supplement_buses)

    def _rebuild_channels_from_branches(self) -> None:
        for line in self.lines or []:
            accs, acvs = collect_line_channels(line)
            line.accs = accs
            line.acvs = acvs
            line.anas = dedup_channels_by_index(accs + acvs)
        for tr in self.transformers or []:
            accs, acvs = collect_transformer_channels(tr)
            tr.accs = accs
            tr.acvs = acvs
            tr.anas = dedup_channels_by_index(accs + acvs)

    def _validate_channels_consistency(self) -> None:
        for line in self.lines or []:
            exp_accs, exp_acvs = collect_line_channels(line)
            if [a.index for a in (line.accs or [])] != [a.index for a in exp_accs]:
                line.accs = exp_accs
            if [a.index for a in (line.acvs or [])] != [a.index for a in exp_acvs]:
                line.acvs = exp_acvs
            exp_anas = dedup_channels_by_index(exp_accs + exp_acvs)
            if [a.index for a in (line.anas or [])] != [a.index for a in exp_anas]:
                line.anas = exp_anas
        for tr in self.transformers or []:
            exp_accs, exp_acvs = collect_transformer_channels(tr)
            if [a.index for a in (tr.accs or [])] != [a.index for a in exp_accs]:
                tr.accs = exp_accs
            if [a.index for a in (tr.acvs or [])] != [a.index for a in exp_acvs]:
                tr.acvs = exp_acvs
            exp_anas = dedup_channels_by_index(exp_accs + exp_acvs)
            if [a.index for a in (tr.anas or [])] != [a.index for a in exp_anas]:
                tr.anas = exp_anas

    def _sync_transformer_winding_bus_id(
        self,
        supplement_buses: dict[tuple[str, TransWindLocation, int | None], Bus],
    ) -> None:
        if not supplement_buses or not self.transformers:
            return
        index_to_bus: dict[int, Bus] = {
            a.index: bus for bus in supplement_buses.values() for a in (bus.acvs or [])
        }
        for tr in self.transformers:
            for tw in tr.trans_winds:
                if tw.bus_id != 0:
                    continue
                vol = tw.voltage
                candidate_indices = [
                    getattr(vol, attr).index
                    for attr in ("ua", "ub", "uc")
                    if getattr(vol, attr) is not None
                ]
                if not candidate_indices:
                    continue
                bus = index_to_bus.get(candidate_indices[0])
                if bus is not None and all(
                    index_to_bus.get(idx) is bus for idx in candidate_indices
                ):
                    tw.bus_id = bus.index
