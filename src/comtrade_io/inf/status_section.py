#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.channel.status import Status
from comtrade_io.type import Contact, DigitalChannelFlag, DigitalChannelType, Phase

class StatusSection(Status):
    """模拟部件模型"""

    @classmethod
    def from_dict(cls, data: dict) -> 'Status':
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

        return status_obj
