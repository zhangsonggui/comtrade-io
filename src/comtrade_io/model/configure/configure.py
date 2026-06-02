#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field, model_serializer

from comtrade_io.model.description import (
    ChannelNum,
    Header,
    Segment,
    SamplingTimeQuality,
    Sampling,
    TimeInfo,
    PrecisionTime,
)
from comtrade_io.model.channel.analog import Analog
from comtrade_io.model.channel.status import Status
from comtrade_io.model.type import DataType


class Configure(BaseModel):
    """
    cfg对象类

    参数:
        description(Header): 配置文件头
        channel_num(ChannelNum): 通道数量
        analogs(list[Analog]): 模拟量通道
        statuses(list[Status]): 数字量通道
        sampling(Sampling): 采样信息
        start_time(PrecisionTime): 故障文件开始时间
        fault_time(PrecisionTime): 故障时间
        data_type(DataType): 录波文件数据格式
        timemult(float): 时标倍率因子
        time_info(TimeInfo): 时间信息及与UTC时间关系
        sampling_time_quality(SamplingTimeQuality): 采样时间品质
    """

    header: Header = Field(description="配置文件头")
    channel_num: ChannelNum = Field(description="通道数量")
    analogs: dict[int, Analog] = Field(default_factory=dict, description="模拟量通道")
    statuses: dict[int, Status] = Field(default_factory=dict, description="数字量通道")
    sampling: Sampling = Field(default_factory=Sampling, description="采样信息")
    start_time: PrecisionTime = Field(
        default_factory=PrecisionTime, description="故障文件开始时间"
    )
    fault_time: PrecisionTime = Field(
        default_factory=PrecisionTime, description="故障时间"
    )
    data_type: DataType = Field(default=DataType.BINARY, description="录波文件数据格式")
    timemult: float = Field(default=1.0, description="时标倍率因子")
    time_info: TimeInfo | None = Field(
        default=None, description="时间信息及与UTC时间关系"
    )
    sampling_time_quality: SamplingTimeQuality | None = Field(
        default=None, description="采样时间品质"
    )

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        """
        在序列化时将字典转换成列表
        """
        data = handler(self)
        data["analogs"] = list(self.analogs.values())
        data["statuses"] = list(self.statuses.values())
        return data

    def __str__(self):
        """
        返回对象的字符串表示形式

        该方法扩展了父类的__str__方法，在其基础上添加了当前对象的所有属性信息，
        包括文件头、通道数量、模拟量通道、数字量通道、采样信息、开始时间、故障时间、数据格式、时标倍率因子、时间信息及与UTC时间关系、采样时间品质等信息。

        Returns:
            str: 完整的字符串表示形式
        """
        cfg_content = ""
        cfg_content += self.header.__str__() + "\n"
        cfg_content += self.channel_num.__str__() + "\n"
        for analog in self.analogs.values():
            cfg_content += analog.__str__() + "\n"
        for status in self.statuses.values():
            cfg_content += status.__str__() + "\n"
        cfg_content += self.sampling.__str__() + "\n"
        cfg_content += self.start_time.__str__() + "\n"
        cfg_content += self.fault_time.__str__() + "\n"
        cfg_content += self.data_type.value + "\n"
        cfg_content += str(self.timemult)
        if self.time_info:
            cfg_content += "\n" + self.time_info.__str__()
        if self.sampling_time_quality:
            cfg_content += "\n" + self.sampling_time_quality.__str__()
        return cfg_content

    def get_analog(self, index: int) -> Analog | None:
        """
        按通道的an(index)获取模拟量通道
        参数:
            index: 通道索引
        返回:
            模拟量通道对象，不存在返回None
        """
        return self.analogs.get(index)

    def get_status(self, index: int) -> Status | None:
        """
        按通道的an(index)获取状态量通道
        参数:
            index: 通道索引
        返回:
            数字量通道对象，不存在返回None
        """
        return self.statuses.get(index)

    def get_sampling_segment(self, index: int) -> Segment | None:
        """
        按采样段号获取该采样段的采样频率和结束采样点
        参数:
            index: 采样段号，从1开始
        返回:
            采样段对象，不存在返回None
        """
        if not (1 <= index <= len(self.sampling.segments)):
            return None
        return self.sampling.segments[index - 1]
