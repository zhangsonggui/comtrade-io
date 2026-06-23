#!/usr/bin/env python
# -*- coding: utf-8 -*-

from comtrade_io.model.description import (
    ChannelNum,
    Description,
    Header,
    Sampling,
    Segment,
)
from comtrade_io.model.type import DataType, Version
from comtrade_io.parser.description.date_time_parser import format_time
from comtrade_io.utils import get_logger

logger = get_logger()


class DescriptionSection:
    """文件描述节解析

    解析 INF 中的 File_Description 节，提取并映射到完整的 Description 模型。
    支持的 INF 字段：
        - Station_Name / Recording_Device_ID / Revision_Year → header / 顶层字段
        - Total_Channel_Count / Analog_Channel_Count / Status_Channel_Count → channel_num
        - Line_Frequency / Sample_Rate_#N / End_Sample_Rate_#N → sampling
        - File_Start_Time / Trigger_Time → datetime
        - File_Type → DataType
        - Time_Multiplier → timemult
    """

    @classmethod
    def from_dict(cls, data: dict) -> Description:
        """从字典创建 Description 对象

        参数:
            data: 文件描述节键值对

        返回:
            Description: 完整的描述文件对象
        """
        station_name = data.get("Station_Name", "")
        rec_dev_name = data.get("Recording_Device_ID", "")
        version_str = data.get('Revision_Year', '1991')
        version = Version.from_value(version_str)

        description = Description(
            header=Header(
                station=station_name,
                recorder=rec_dev_name,
                version=version,
            ),
        )

        total = data.get("Total_Channel_Count")
        analog = data.get("Analog_Channel_Count")
        status = data.get("Status_Channel_Count")
        if total or analog or status:
            description.channel_num = ChannelNum(
                total=int(total) if total else 0,
                analog=int(analog) if analog else 0,
                status=int(status) if status else 0,
            )

        freq = data.get("Line_Frequency")
        sample_rate_count = data.get("Sample_Rate_Count")
        if freq or sample_rate_count:
            sampling = Sampling()
            if freq:
                sampling.freq = float(freq)
            if sample_rate_count:
                for i in range(1, int(sample_rate_count) + 1):
                    samp = data.get(f"Sample_Rate_#{i}")
                    end = data.get(f"End_Sample_Rate_#{i}")
                    if samp and end:
                        sampling.segments.append(
                            Segment(samp=int(float(samp)), end_point=int(float(end)))
                        )
            description.sampling = sampling

        for attr, key in [
            ("file_start_time", "File_Start_Time"),
            ("trigger_time", "Trigger_Time"),
        ]:
            time_str = data.get(key)
            if time_str:
                try:
                    setattr(description, attr, format_time(time_str))
                except (ValueError, IndexError):
                    pass

        file_type = data.get("File_Type")
        if file_type:
            try:
                description.data_type = DataType.from_value(file_type)
            except ValueError:
                pass

        timemult = data.get("Time_Multiplier")
        if timemult:
            description.timemult = float(timemult)

        logger.debug(
            f"描述节解析: station={station_name}, "
            f"recorder={rec_dev_name}, version={version_str}"
        )
        return description
