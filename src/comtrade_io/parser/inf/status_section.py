from ...model.channel.status import Status
from ...model.type import (
    Contact,
    DigitalChannelFlag,
    DigitalChannelType,
    Phase,
)
from ...utils import get_logger

logger = get_logger()


class StatusSection(Status):
    """开关量通道解析模型

    继承自 Status 模型，提供从 INF 字典数据创建 Status 对象的工厂方法。
    同时支持通道定义段和通道参数段的字段映射。
    """

    @classmethod
    def from_dict(cls, data: dict) -> 'Status':
        """从字典数据创建 Status 对象

        支持两种数据来源:
        1. 通道定义段: Channel_ID, Phase_ID, Normal_State, Monitored_Component
        2. 通道参数段: level(type), type(flag), obj(equipment_no)

        参数:
            data: 包含通道字段的字典

        返回:
            Status: 创建的开关量通道对象
        """
        index = data.get("index", None)
        name = data.get("Channel_ID") or data.get("name")
        phase = Phase.from_value(data.get("Phase_ID", "") or data.get("phase", ""))
        reference = data.get("Monitored_Component") or data.get("reference", "")
        contact_raw = data.get("Normal_State")
        if contact_raw is not None:
            contact = Contact.from_value(contact_raw, Contact.NormallyOpen)
        else:
            contact = Contact.NormallyOpen

        status_obj = Status(
            index=index, name=name, phase=phase, reference=reference, contact=contact
        )

        # 参数段中的 level 对应 DigitalChannelType，type 对应 DigitalChannelFlag
        level_val = data.get("level")
        type_val = data.get("type")
        if level_val:
            try:
                dtype = DigitalChannelType.from_name(level_val)
                status_obj.type = dtype
            except ValueError:
                pass
        if type_val:
            try:
                flag = DigitalChannelFlag.from_name(type_val)
                status_obj.flag = flag
                # 如果 level 未指定，从 flag 推导 type
                if status_obj.type is None and flag.type:
                    status_obj.type = flag.type
            except ValueError:
                pass

        obj_val = data.get("obj") or data.get("Obj")
        if obj_val:
            status_obj.equipment_no = obj_val

        idx_org = data.get("idx_org")
        if idx_org is not None:
            status_obj.idx_org = int(idx_org) if isinstance(idx_org, str) else idx_org

        logger.debug(
            f"开关量通道 {index}: {name}, {phase.value}, contact={contact_raw}"
        )
        return status_obj
