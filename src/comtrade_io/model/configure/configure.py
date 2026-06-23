#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field, model_serializer

from comtrade_io.model.channel.analog import Analog
from comtrade_io.model.channel.status import Status
from comtrade_io.model.description import Description, Segment
from comtrade_io.parser.description.data_time_parser import format_datetime_for_cfg


class Configure(BaseModel):
    """
    cfg对象类

    参数:
        description(Description): 描述信息（包含文件头、通道数、采样、时间、数据格式等）
        analogs(dict[int, Analog]): 模拟量通道
        statuses(dict[int, Status]): 数字量通道
    """

    description: Description = Field(
        default_factory=Description, description="描述信息"
    )
    analogs: dict[int, Analog] = Field(default_factory=dict, description="模拟量通道")
    statuses: dict[int, Status] = Field(default_factory=dict, description="数字量通道")

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        data = handler(self)
        data["analogs"] = list(self.analogs.values())
        data["statuses"] = list(self.statuses.values())
        if "description" in data and isinstance(data["description"], dict):
            data.update(data.pop("description"))
        return data

    def __str__(self):
        cfg_content = ""
        cfg_content += self.description.header.__str__() + "\n"
        cfg_content += self.description.channel_num.__str__() + "\n"
        for analog in self.analogs.values():
            cfg_content += analog.__str__() + "\n"
        for status in self.statuses.values():
            cfg_content += status.__str__() + "\n"
        cfg_content += self.description.sampling.__str__() + "\n"
        cfg_content += format_datetime_for_cfg(self.description.file_start_time) + "\n"
        cfg_content += format_datetime_for_cfg(self.description.trigger_time) + "\n"
        cfg_content += self.description.data_type.value + "\n"
        cfg_content += str(self.description.timemult)
        if self.description.time_info:
            cfg_content += "\n" + self.description.time_info.__str__()
        if self.description.sampling_time_quality:
            cfg_content += "\n" + self.description.sampling_time_quality.__str__()
        return cfg_content

    def get_analog(self, index: int) -> Analog | None:
        return self.analogs.get(index)

    def get_status(self, index: int) -> Status | None:
        return self.statuses.get(index)

    def get_sampling_segment(self, index: int) -> Segment | None:
        if not (1 <= index <= len(self.description.sampling.segments)):
            return None
        return self.description.sampling.segments[index - 1]
