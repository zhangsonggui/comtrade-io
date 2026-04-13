#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.channel.status import Status
from comtrade_io.type import Contact, Phase


class StatusSection(Status):
    """模拟部件模型"""

    @classmethod
    def from_dict(cls, data: dict) -> 'Status':
        index = data.get("index", None)
        name = data.get("Channel_ID", None)
        phase = Phase.from_value(data.get("Phase_ID", ""))
        reference = data.get("Monitored_Component", "")
        contact = Contact.from_value(data.get("Normal_State", Contact.NormallyOpen))

        return Status(
                index=index,
                name=name,
                phase=phase,
                reference=reference,
                contact=contact
        )
