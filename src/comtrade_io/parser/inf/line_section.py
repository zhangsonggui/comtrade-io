from ...model.channel import Analog, Status
from ...model.equipment import Line
from ...model.equipment.branch import ACCBranch
from ...model.equipment.line_param import (
    Capacitance,
    Impedance,
    MutualInductance,
)
from ...model.type import CurrentBranchNum
from .equipment_section import (
    EquipmentSection,
    parse_four_values,
    parse_number_with_unit,
    parse_two_values,
)
from ...utils import get_logger

logger = get_logger()


class LineSection(EquipmentSection):
    """线路部件解析

    继承 EquipmentSection，增加线路特有的属性解析：
    - LENGTH: 线路长度
    - RX: 阻抗参数（r1, x1, r0, x0）
    - CG: 电容参数（c1, g1, c0, g0）
    - MRX: 互感参数（mr0, mx0）
    - 根据电流通道数推断分支数
    """

    @classmethod
    def from_dict(
        cls,
        data: dict,
        analog_channels: dict[int, Analog],
        status_channels: dict[int, Status],
    ) -> "Line":
        """从字典生成线路模型

        解析线路长度、阻抗、电容、互感等电气参数。

        参数:
            data: 线路节键值对
            analog_channels: 模拟通道字典
            status_channels: 开关量通道字典

        返回:
            Line: 线路对象，含完整的阻抗、电容、互感参数
        """
        equipment = super().from_dict(data, analog_channels, status_channels)
        line = Line(
            index=equipment.index,
            uuid=equipment.uuid,
            name=equipment.name,
            stas=equipment.stas,
            acvs=equipment.acvs,
            accs=equipment.accs,
        )

        # 解析线路长度
        length_str = data.get("LENGTH", "0(km)")
        line.line_length = parse_number_with_unit(length_str)

        # 解析阻抗参数 RX: r1, x1, r0, x0
        rx_str = data.get("RX", "0, 0, 0, 0")
        rx_values = parse_four_values(rx_str)
        line.impedance = Impedance(
            r1=rx_values[0] if len(rx_values) > 0 else 0.0,
            x1=rx_values[1] if len(rx_values) > 1 else 0.0,
            r0=rx_values[2] if len(rx_values) > 2 else 0.0,
            x0=rx_values[3] if len(rx_values) > 3 else 0.0,
        )

        # 解析电容参数 CG: c1, g1, c0, g0
        cg_str = data.get("CG", "0, 0, 0, 0")
        cg_values = parse_four_values(cg_str)
        line.capacitance = Capacitance(
            c1=cg_values[0] if len(cg_values) > 0 else 0.0,
            g1=cg_values[1] if len(cg_values) > 1 else 0.0,
            c0=cg_values[2] if len(cg_values) > 2 else 0.0,
            g0=cg_values[3] if len(cg_values) > 3 else 0.0,
        )

        # 解析互感参数 MRX: mr0, mx0
        mrx_str = data.get("MRX", "0, 0")
        mrx_values = parse_two_values(mrx_str)
        line.mutual_inductance = MutualInductance(
            idx=int(data.get("index", 0)),
            mr0=mrx_values[0] if len(mrx_values) > 0 else 0.0,
            mx0=mrx_values[1] if len(mrx_values) > 1 else 0.0,
        )
        line.currents = ACCBranch.from_analog_channels(line.accs)
        if len(line.currents) > 1:
            line.current_bran_num = CurrentBranchNum.B2

        logger.debug(
            f"线路 {equipment.index}: {equipment.name}, "
            f"长度={line.line_length}km, 阻抗段数={len(line.currents)}"
        )
        return line
