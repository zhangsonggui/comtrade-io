#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import cast

from pydantic import BaseModel

from comtrade_io.model.description import Sampling
from comtrade_io.model.configure import Configure
from comtrade_io.parser.cfg.analog_parser import AnalogParser
from comtrade_io.parser.description import (
    HeaderParser,
    ChannelNumParser,
    SegmentParser,
    PrecisionTimeParser,
    TimeInfoParser,
    SamplingTimeQualityParser,
)
from comtrade_io.parser.cfg.status_parser import StatusParser
from comtrade_io.model.comtrade_file import ComtradeFile
from comtrade_io.model.type import DataType
from comtrade_io.utils import get_logger, parse_float, text_split

logger = get_logger()


class CfgFileParser(BaseModel):
    """CFG 配置文件解析器
    Cfg 配置文件包含 CFG 头部、数据质量、采样、采样时间、通道数、数据、注释等信息。
    """

    @staticmethod
    def from_str(_str: str) -> Configure:
        """从逗号分隔的文本字符串反序列化配置对象

        该方法将包含换行符的配置文件字符串解析为Configure对象。
        解析过程包括：文件头、通道数量、模拟量通道、数字量通道、采样信息、时间信息等。

        参数:
            _str: 包含完整配置文件内容的字符串，以换行符分隔各行

        返回:
            Configure: 解析后的配置对象
        """
        logger.debug("开始解析CFG文件内容")
        parts = text_split(_str, "\n")

        # 第1行: 文件头
        header = HeaderParser.from_str(parts[0])
        logger.debug(
            f"解析文件头: station={header.station}, "
            f"recorder={header.recorder}, version={header.version}"
        )

        # 第2行: 通道数量
        channel_num = ChannelNumParser.from_str(parts[1])
        logger.debug(
            f"解析通道数量: total={channel_num.total}, "
            f"analog={channel_num.analog}, status={channel_num.status}"
        )

        # 跳过通道信息行(模拟量行+数字量行)，处理采样信息
        cursor_row = channel_num.total + 2

        # 采样频率
        sampling = Sampling(freq=float(parts[cursor_row]))
        logger.debug(f"解析采样频率: {sampling.freq}")

        # 采样段
        segment_len = int(parts[cursor_row + 1])
        logger.debug(f"采样段数量: {segment_len}")
        for i in range(segment_len):
            segment_str = parts[cursor_row + 2 + i]
            if segment_str:
                segment = SegmentParser.from_str(segment_str)
                if segment is None:
                    continue
                sampling.segments.append(segment)
        cursor_row += segment_len + 2

        # 开始时间和故障时间
        start_time_str = parts[cursor_row]
        start_time = PrecisionTimeParser.from_str(start_time_str)
        fault_time_str = parts[cursor_row + 1]
        fault_time = PrecisionTimeParser.from_str(fault_time_str)
        logger.debug(f"解析开始时间: {start_time.time}, 故障时间: {fault_time.time}")

        # 数据格式
        data_type_str = parts[cursor_row + 2].strip(",")
        data_type = cast(DataType, DataType.from_value(data_type_str))
        logger.debug(f"解析数据格式: {data_type}")

        configure = Configure(
            header=header,
            channel_num=channel_num,
            sampling=sampling,
            start_time=start_time,
            fault_time=fault_time,
            data_type=data_type,
        )
        cursor_row += 3

        # 可选字段: 时标倍率因子
        if (part_len := len(parts)) > cursor_row:
            configure.timemult = parse_float(parts[cursor_row])
            logger.debug(f"解析时标倍率因子: {configure.timemult}")

        # 可选字段: 时间信息
        if part_len > (cursor_row + 1):
            configure.time_info = TimeInfoParser.from_str(parts[cursor_row + 1])
            logger.debug(
                f"解析时间信息: time_code={configure.time_info.time_code}, "
                f"local_code={configure.time_info.local_code}"
            )

        # 可选字段: 采样时间品质
        if part_len > (cursor_row + 2):
            configure.sampling_time_quality = SamplingTimeQualityParser.from_str(
                parts[cursor_row + 2]
            )
            logger.debug(
                f"解析采样时间品质: tmq_code={configure.sampling_time_quality.tmq_code}"
            )

        # 解析模拟量通道
        logger.debug(f"开始解析{channel_num.analog}个模拟量通道")
        for i in range(channel_num.analog):
            analog = AnalogParser.from_string(parts[i + 2])
            configure.analogs[analog.index] = analog
        logger.debug(f"模拟量通道解析完成")

        # 解析数字量通道
        cursor_row = channel_num.analog + 2
        logger.debug(f"开始解析{channel_num.status}个数字量通道")
        for i in range(channel_num.status):
            status = StatusParser.from_string(parts[i + cursor_row])
            configure.statuses[status.index] = status
        logger.debug(f"数字量通道解析完成")

        logger.info("CFG文件内容解析完成")
        return configure

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> Configure | None:
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
            logger.warning(f"CFG配置文件不可用: {cf.cfg_path.path}")
            return None
        cfg_path = cf.cfg_path.path
        logger.debug(f"正在读取配置文件: {cfg_path}")
        try:
            cfg_content = cfg_path.read_text(encoding="GBK", errors="replace")
        except UnicodeDecodeError:
            logger.warning(f"配置文件{cfg_path}编码不是GBK编码，尝试使用UTF8解析")
            try:
                cfg_content = cfg_path.read_text(encoding="utf-8", errors="replace")
            except UnicodeDecodeError:
                logger.error(f"配置文件{cfg_path}编码不是UTF8编码，请检查文件编码")
                raise
        try:
            return CfgFileParser.from_str(cfg_content)
        except IndexError as e:
            error_str = f"配置文件{cfg_path}行数不对应,{str(e)}"
            logger.error(error_str)
            raise ValueError(f"配置文件{cfg_path}行数不对应,{e}")

    @staticmethod
    def write_file(config: Configure, output_file_path: ComtradeFile | Path | str):
        """将配置写入文件

        将当前Configure对象序列化,使用GBK编码写入指定的CFG配置文件。

        参数:
            output_file_path: 输出文件路径，可以是字符串或Path对象
        """
        output_file_path = ComtradeFile.from_path(output_file_path)
        cfg_path = output_file_path.cfg_path.path

        with open(cfg_path, "w", encoding="gbk", errors="ignore") as f:
            f.write(config.__str__())
        logger.info(f"配置文件{cfg_path}写入成功")
        return True
