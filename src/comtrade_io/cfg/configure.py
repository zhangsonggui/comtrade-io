#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional, cast

from pydantic import BaseModel, Field, model_serializer

from comtrade_io.base.precision_time import PrecisionTime
from comtrade_io.cfg.analog_dispose import AnalogDispose
from comtrade_io.cfg.channel_num import ChannelNum
from comtrade_io.cfg.header import Header
from comtrade_io.cfg.sampling import Sampling
from comtrade_io.cfg.sampling_time_quality import SamplingTimeQuality
from comtrade_io.cfg.segment import Segment
from comtrade_io.cfg.status_dispose import StatusDispose
from comtrade_io.cfg.time_info import TimeInfo
from comtrade_io.channel.analog import Analog
from comtrade_io.channel.status import Status
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.type import DataType
from comtrade_io.utils import get_logger, parse_float, text_split

logging = get_logger()


class Configure(BaseModel):
    """
    cfg对象类

    参数:
        header(Header): 配置文件头
        channel_num(ChannelNum): 通道数量
        analogs(list[Analog]): 模拟量通道
        digitals(list[Digital]): 数字量通道
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
    start_time: PrecisionTime = Field(default_factory=PrecisionTime, description="故障文件开始时间")
    fault_time: PrecisionTime = Field(default_factory=PrecisionTime, description="故障时间")
    data_type: DataType = Field(default=DataType.BINARY, description="录波文件数据格式")
    timemult: float = Field(default=1.0, description="时标倍率因子")
    time_info: Optional[TimeInfo] = Field(default=None, description="时间信息及与UTC时间关系")
    sampling_time_quality: Optional[SamplingTimeQuality] = Field(default=None, description="采样时间品质")

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        """
        在序列化时将字典转换成列表
        """
        data = handler(self)
        data['analogs'] = list(self.analogs.values())
        data['statuses'] = list(self.statuses.values())
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

    @classmethod
    def from_str(cls, _str: str) -> 'Configure':
        """从逗号分隔的文本字符串反序列化配置对象

        该方法将包含换行符的配置文件字符串解析为Configure对象。
        解析过程包括：文件头、通道数量、模拟量通道、数字量通道、采样信息、时间信息等。

        参数:
            _str: 包含完整配置文件内容的字符串，以换行符分隔各行

        返回:
            Configure: 解析后的配置对象
        """
        parts = text_split(_str, "\n")
        # 处理文件头和采样通道数量
        header = Header.from_str(parts[0])
        channel_num = ChannelNum.from_str(parts[1])
        # 跳过通道信息,处理采样频率、采样段、采样时间、数据格式信息
        cursor_row = channel_num.total + 2
        sampling = Sampling(freq=float(parts[cursor_row]))
        segment_len = int(parts[cursor_row + 1])
        for i in range(segment_len):
            segment_str = parts[cursor_row + 2 + i]
            if segment_str:
                segment = Segment.from_str(segment_str)
                if segment is None:
                    continue
                sampling.segments.append(segment)
        cursor_row += segment_len + 2
        start_time_str = parts[cursor_row]
        start_time = PrecisionTime.from_str(start_time_str)
        fault_time_str = parts[cursor_row + 1]
        fault_time = PrecisionTime.from_str(fault_time_str)
        data_type_str = parts[cursor_row + 2].strip(',')
        data_type = cast(DataType, DataType.from_value(data_type_str))
        configure = cls(header=header,
                        channel_num=channel_num,
                        sampling=sampling,
                        start_time=start_time,
                        fault_time=fault_time,
                        data_type=data_type)  # type: ignore[arg-type]
        cursor_row += 3
        if (part_len := len(parts)) > cursor_row:
            configure.timemult = parse_float(parts[cursor_row])
        if part_len > (cursor_row + 1):
            configure.time_info = TimeInfo.from_str(parts[cursor_row + 1])
        if part_len > (cursor_row + 2):
            configure.sampling_time_quality = SamplingTimeQuality.from_str(parts[cursor_row + 2])
        # 处理模拟量、数字量通道
        for i in range(channel_num.analog):
            analog = AnalogDispose.from_string(parts[i + 2])
            configure.analogs[analog.index] = analog
        cursor_row = channel_num.analog + 2
        for i in range(channel_num.status):
            status = StatusDispose.from_string(parts[i + cursor_row])
            configure.statuses[status.index] = status

        return configure

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> 'Configure|None':
        """从文件名中解析配置文件

        读取指定文件路径的CFG配置文件，并将其解析为Configure对象。
        支持多种输入类型：字符串路径、Path对象或ComtradeFile对象。

        参数:
            file_name: 配置文件路径，可以是字符串、Path对象或ComtradeFile对象

        返回:
            Configure: 解析后的配置对象；如果文件禁用则返回None
        """
        cf = ComtradeFile.from_path(file_path=file_name)

        if not cf.cfg_path.is_enabled():
            return None
        cfg_path = cf.cfg_path.path
        try:
            cfg_content = cfg_path.read_text(encoding="GBK")
        except UnicodeDecodeError:
            logging.warning(f"配置文件{cfg_path}编码不是GBK编码，尝试使用UTF8解析")
            try:
                cfg_content = cfg_path.read_text(encoding="utf-8", errors='replace')
            except UnicodeDecodeError:
                logging.error(f"配置文件{cfg_path}编码不是UTF8编码，请检查文件编码")
                raise
        try:
            return Configure.from_str(cfg_content)
        except IndexError as e:
            error_str = f"配置文件{cfg_path}行数不对应,{str(e)}"
            logging.error(error_str)
            raise ValueError(f"配置文件{cfg_path}行数不对应,{e}")

    def write_file(self, output_file_path: ComtradeFile | Path | str):
        """将配置写入文件

        将当前Configure对象序列化并写入指定的CFG配置文件。
        写入使用GBK编码以兼容COMTRADE标准。

        参数:
            output_file_path: 输出文件路径，可以是字符串或Path对象
        """
        output_file_path = ComtradeFile.from_path(output_file_path)
        cfg_path = output_file_path.cfg_path.path

        with open(cfg_path, "w", encoding="gbk") as f:
            f.write(self.__str__())
        logging.info(f"配置文件{cfg_path}写入成功")
        return True

    def get_analog(self, index: int) -> Optional[Analog]:
        """
        按通道的an(index)获取模拟量通道
        参数:
            index: 通道索引
        返回:
            模拟量通道对象，不存在返回None
        """
        return self.analogs.get(index)

    def get_digital(self, index: int) -> Optional[Status]:
        """
        按通道的an(index)获取数字量通道
        参数:
            index: 通道索引
        返回:
            数字量通道对象，不存在返回None
        """
        return self.statuses.get(index)

    def get_sampling_segment(self, index: int) -> Optional[Segment]:
        """
        按采样段号获取该采样段的采样频率和结束采样点
        参数:
            index: 采样段号，从1开始
        返回:
            数字量通道对象，不存在返回None
        """
        if 1 <= index <= len(self.sampling.segments):
            return None
        return self.sampling.segments[index - 1]
