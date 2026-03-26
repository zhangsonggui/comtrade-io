#!/usr/bin/env python
# -*- coding: utf-8 -*-
import struct
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from comtrade_io.cfg import Configure
from comtrade_io.cfg.sampling import Sampling
from comtrade_io.cfg.segment import Segment
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.type import DataType
from comtrade_io.utils import get_logger
from pydantic import BaseModel, ConfigDict, Field

logging = get_logger()

CYCLE_TIME_MS = 20.0


class DataContent(BaseModel):
    """
    DAT文件解析器

    参数:
        cfg(Configure): 配置
        file_name(Path): dat文件路径
        data(pd.DataFrame): 数据内容，可选
    返回值
        DataContent|None(pandas.DataFrame): 数据对象
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cfg: Configure = Field(..., description="配置文件")
    file_name: Path | ComtradeFile | str = Field(..., description="dat文件路径")
    data: pd.DataFrame = Field(default=None, description="数据内容")

    def model_post_init(self, context: Any):
        cf = ComtradeFile.from_path(file_path=self.file_name)
        if not cf.dat_path.is_enabled():
            return
        self.file_name = cf.dat_path.path
        self.data = self.read()
        if self.data.shape[0] != self.cfg.sampling.segments[-1].end_point:
            logging.warning(
                f"实际读取数据点：{self.data.shape[0]}与配置文件数据点{self.cfg.sampling.segments[-1].end_point}不一致，根据采样点时间进行修正")
            self.verify_and_recalculate_sampling()

    def get_data(
            self,
            index: int,
            data_type: str = "analog",
            start_point: int = 1,
            end_point: int = None,
    ):
        """
        获取指定通道的数据

        根据data_type参数获取不同类型的数据：
        - "point": 获取数据点索引列（第0列）
        - "time": 获取时间戳列（第1列）
        - "analog": 获取模拟量通道数据
        - "digital": 获取开关量通道数据

        参数:
            index: 通道索引（从0开始）
            data_type: 数据类型，可选值为 "point"、"time"、"analog"、"digital"，默认为 "analog"
            start_point: 起始列（保留参数，当前未使用）
            end_point: 结束列（保留参数，当前未使用）

        返回:
            np.ndarray: 返回一维numpy数组，如果列索引超出范围则返回None
        """
        if self.data is None:
            return None

        data_type = data_type.lower()

        # 根据数据类型计算列索引
        # DataFrame列结构：第0列为索引，第1列为时间戳，第2列开始为模拟量，之后为开关量
        col_index_map = {
            "point" : 0,
            "time"  : 1,
            "analog": 2,
            "digital": self.cfg.channel_num.analog + 2
        }

        base_col = col_index_map.get(data_type, 2)

        # 对于模拟量和开关量，需要加上通道索引
        if data_type in ("analog", "digital"):
            col_index = base_col + index
        else:
            col_index = base_col
        # 检查采样点是否在有效范围内
        if not end_point:
            end_point = self.data.shape[0]
        if start_point > 0:
            start_point -= 1
        if start_point < 0 or start_point >= end_point or end_point > self.data.shape[0]:
            return None
        # 检查列索引是否在有效范围内
        if 0 <= col_index < self.data.shape[1]:
            return self.data.iloc[start_point:end_point, col_index].to_numpy()

        return None

    def read(self) -> pd.DataFrame | None:
        """
        读取数据文件,返回数据对象(pandas.DataFrame)
        """
        expected_rows = self.cfg.sampling.segments[-1].end_point
        expected_cols = self.cfg.channel_num.total + 2
        if self.cfg.data_type == DataType.ASCII:
            content = self.from_ascii_file(expected_rows, expected_cols)
        else:
            content = self.from_binary_file(expected_rows)
        # 设置数据格式
        type_mapping = {i: "int32" for i in range(2)}
        type_mapping.update(
            {i + 2: "float64" for i in range(self.cfg.channel_num.analog)}
        )
        type_mapping.update(
            {
                self.cfg.channel_num.analog + 2 + i: "int32"
                for i in range(self.cfg.channel_num.digital)
            }
        )
        content = content.astype(type_mapping)

        # 将模拟量的原始采样值转换为瞬时值数值
        if content is None:
            return None

        # 使用向量化操作替代循环，提升性能
        analog_count = self.cfg.channel_num.analog
        if analog_count > 0:
            analog_list = list(self.cfg.analogs.values())
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            cols = list(range(2, 2 + analog_count))
            content.iloc[:, cols] = content.iloc[:, cols] * multipliers + offsets

        return content

    def from_ascii_file(self, expected_rows, expected_cols):
        """
        读取ASCII格式的数据文件
        """
        try:
            content = pd.read_csv(
                self.file_name,
                sep=",",
                na_values=["", "NA", "null", "NULL", "None", "-", "NaN"],
                keep_default_na=False,
                header=None,
            )
            content = content.fillna(0)
        except Exception as e:
            raise ValueError(f"读取数据文件失败:{str(e)}")
        actual_rows, actual_cols = content.shape
        # 读取行列号和配置文件一致
        if actual_cols == expected_cols and actual_rows == expected_rows:
            return content
        # 实际读取的采样点和配置文件的采样点数量不一致
        if actual_rows != expected_rows:
            # 实际读取的采样点大于配置文件
            if actual_rows > expected_rows:
                try:
                    pd.isna(content.iloc[actual_rows, 0])
                    logging.warning(
                        f"数据文件{self.file_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},需要重新计算采样信息"
                    )
                except:
                    logging.warning(
                        f"数据文件{self.file_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},数据类型错误进行剪切"
                    )
                    content = content.iloc[:expected_rows, :]
        # 实际读取的列和通道数量不一样
        if actual_cols != expected_cols:
            digital_cols = actual_cols - self.cfg.channel_num.analog - 2
            if digital_cols < 0:
                logging.error(
                    f"数据文件{self.file_name}数据拆分错误，期望最少读取{self.cfg.channel_num.analog + 2}列，实际读取{actual_cols}列，不符合返回空数据！"
                )
                return None
            else:
                logging.error(
                    f"数据文件{self.file_name}数据拆分错误，期望读取{self.cfg.channel_num.total + 2}列，实际读取{actual_cols}列，丢弃数字量数据！"
                )
                content = content.iloc[:, : self.cfg.channel_num.analog + 2]
                new_columns = [
                    self.cfg.channel_num.analog + 2 + i
                    for i in range(self.cfg.channel_num.digital)
                ]
                new_data = pd.DataFrame(0, index=content.index, columns=new_columns)
                content = pd.concat([content, new_data], axis=1)
        return content

    def from_binary_file(self, expected_rows):
        """
        读取BINARY格式的数据文件
        """
        # 文件大小
        file_size = self.file_name.stat().st_size
        # 数字量占用字节长度
        digital_word_count = (self.cfg.channel_num.digital + 15) // 16
        # 单个模拟量占用字节长度
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        analog_dtype = np.int32 if self.cfg.data_type in INT32_TYPES else np.int16
        # 单个采样点结构
        dt = np.dtype(
            [
                ("index", np.int32, 1),  # 数据点索引
                ("timestamp", np.int32, 1),  # 相对时间
                ("analog", analog_dtype, self.cfg.channel_num.analog),  # 模拟量
                ("digital", np.uint16, digital_word_count),  # 开关量（以16位字为单位）
            ]
        )
        # 当个采样点的字节长度
        item_size = dt.itemsize
        sample_count = file_size // item_size

        try:
            binary_data = self.file_name.read_bytes()
        except Exception as e:
            logging.error(f"读取{self.file_name}文件中的二进制数据失败: {e}")
            return None

        if sample_count == expected_rows:
            samples = np.frombuffer(binary_data, dtype=dt)
        else:
            logging.warning(
                f"期望采样点数量：{expected_rows},数据文件不是{item_size}的整数倍，实际读取{sample_count}个采样点"
            )
            samples = np.frombuffer(binary_data, dtype=dt, count=sample_count)

        # 使用向量化操作优化，避免循环逐行构建DataFrame
        index_data = samples["index"].astype(np.int32)
        timestamp_data = samples["timestamp"].astype(np.int32)
        analog_data = samples["analog"].astype(np.float64)

        # 处理数字量：向量化展开比特位
        if self.cfg.channel_num.digital > 0:
            digital_data = samples["digital"].reshape(-1, digital_word_count)
            digital_bytes = digital_data.view(np.uint8).reshape(sample_count, -1)
            bits = np.unpackbits(digital_bytes, axis=1, bitorder="little")
            digital_bits = bits[:, : self.cfg.channel_num.digital]
        else:
            digital_bits = np.zeros((sample_count, 0), dtype=np.int32)

        # 使用np.column_stack高效合并数组
        if self.cfg.channel_num.analog > 0:
            data_array = np.column_stack(
                [index_data, timestamp_data, analog_data, digital_bits]
            )
        else:
            data_array = np.column_stack([index_data, timestamp_data, digital_bits])

        content = pd.DataFrame(data_array)
        return content

    def write_file(self,
                   output_file_path: ComtradeFile | Path | str,
                   data_type: str = "BINARY"):
        output_file_path = ComtradeFile.from_path(output_file_path)
        data_path = output_file_path.dat_path.path

        if data_type.upper() == "ASCII":
            self._write_ascii_dat_file(data_path)
        else:
            self._write_binary_dat_file(data_path)
        return True

    def _write_ascii_dat_file(self, output_file_path: Path | str):
        """
        将数据写入ASCII格式文件

        参数:
            output_file_path: 输出文件路径
        """
        self.data.to_csv(str(output_file_path), header=False, index=False)
        logging.info(f"数据文件{output_file_path}写入成功")

    def _write_binary_dat_file(self, output_file_path: Path | str):
        """
        将数据写入二进制格式文件，符合 COMTRADE 标准格式

        参数:
            output_file_path: 输出文件路径
        """
        analog_int32 = self.cfg.data_type in {DataType.BINARY32, DataType.FLOAT32}
        analog_fmt = "<i" if analog_int32 else "<h"

        analog_count = self.cfg.channel_num.analog
        digital_count = self.cfg.channel_num.digital
        digital_word_count = (digital_count + 15) // 16

        with open(str(output_file_path), "wb") as f:
            for i in range(len(self.data)):
                sample_index = int(float(self.data.iloc[i, 0].real))
                f.write(struct.pack("<i", sample_index))

                sample_time = int(float(self.data.iloc[i, 1].real))
                f.write(struct.pack("<i", sample_time))

                for a in range(analog_count):
                    col = 2 + a
                    if col < self.data.shape[1]:
                        val = self.data.iloc[i, col]
                        ival = int(
                            float(val.real) if hasattr(val, "real") else float(val)
                        )
                    else:
                        ival = 0
                    f.write(struct.pack(analog_fmt, ival))

                for word_idx in range(digital_word_count):
                    digital_word = 0
                    for bit_idx in range(16):
                        channel_idx = word_idx * 16 + bit_idx
                        col = 2 + analog_count + channel_idx
                        if channel_idx < digital_count and col < self.data.shape[1]:
                            bit_val = int(
                                float(self.data.iloc[i, col].real)
                                if hasattr(self.data.iloc[i, col], "real")
                                else float(self.data.iloc[i, col])
                            )
                            if bit_val != 0:
                                digital_word |= 1 << bit_idx
                    f.write(struct.pack("<H", digital_word))
            logging.info(f"数据文件{output_file_path}写入成功")
        return True

    def verify_and_recalculate_sampling(self) -> Sampling:
        """
        校验采样时间并重新计算采样频率
        
        1. 读取data文件中第二列的采样时间（微秒）
        2. 与cfg中的timemult相乘得出真正的采样时间
        3. 根据采样时间间隔重新计算采样频率，将相同采样频率的点放到一起
        4. Segment中的samp是该段的采样频率，end_point是该段最后一个采样点索引
        5. 周波默认20ms
        
        返回:
            Sampling: 重新计算后的采样信息
        """
        if self.data is None or len(self.data) < 2:
            return self.cfg.sampling

        timestamps_us = self.data.iloc[:, 1].to_numpy() * self.cfg.timemult
        time_diffs_us = np.diff(timestamps_us)

        change_indices = np.where(np.diff(time_diffs_us) != 0)[0] + 1
        segment_starts = np.concatenate([[0], change_indices])
        segment_ends = np.concatenate([change_indices, [len(timestamps_us)]])

        segments = [
            Segment(samp=round(1_000_000.0 / time_diffs_us[start]), end_point=end)
            for start, end in zip(segment_starts, segment_ends)
            if time_diffs_us[start] > 0
        ]

        if not segments:
            return self.cfg.sampling

        self.cfg.sampling.segments = segments

        return self.cfg.sampling
