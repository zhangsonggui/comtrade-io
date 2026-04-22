#!/usr/bin/env python
# -*- coding: utf-8 -*-
import struct
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from comtrade_io.cfg import Configure
from comtrade_io.cfg.sampling import Sampling
from comtrade_io.cfg.segment import Segment
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.type import DataType
from comtrade_io.utils import get_logger

logging = get_logger()

CYCLE_TIME_MS = 20.0


class DataContent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    cfg: Configure = Field(..., description="配置文件")
    file_name: Path | ComtradeFile | str | None = Field(default=None, description="dat文件路径")
    dat_text: str | None = Field(default=None, description="DAT数据文本(ASCII格式)")
    dat_bytes: bytes | None = Field(default=None, description="DAT数据字节(二进制格式)")
    data: pd.DataFrame = Field(default=None, description="数据内容")

    def model_post_init(self, context: Any):
        if self.dat_text is not None or self.dat_bytes is not None:
            self.data = self.read_from_memory()
        elif self.file_name is not None:
            cf = ComtradeFile.from_path(file_path=self.file_name)
            if not cf.dat_path.is_enabled():
                return
            self.file_name = cf.dat_path.path
            self.data = self.read()
        else:
            return

        if self.data is not None and self.data.shape[0] != self.cfg.sampling.segments[-1].end_point:
            logging.warning(
                f"实际读取数据点：{self.data.shape[0]}与配置文件数据点{self.cfg.sampling.segments[-1].end_point}不一致，根据采样点时间进行修正")
        self.verify_and_recalculate_sampling()

    def get_data(self, index: int, data_type: str = "analog", start_point: int = 1, end_point: int = None):
        if self.data is None:
            return None

        data_type = data_type.lower()
        col_index_map = {
            "point": 0,
            "time" : 1,
            "analog": 2,
            "status": self.cfg.channel_num.analog + 2
        }

        base_col = col_index_map.get(data_type, 2)

        if data_type in ("analog", "status"):
            col_index = base_col + index
        else:
            col_index = base_col

        if not end_point:
            end_point = self.data.shape[0]
        if start_point > 0:
            start_point -= 1
        if start_point < 0 or start_point >= end_point or end_point > self.data.shape[0]:
            return None
        if 0 <= col_index < self.data.shape[1]:
            return self.data.iloc[start_point:end_point, col_index].to_numpy()

        return None

    def read(self) -> pd.DataFrame | None:
        expected_rows = self.cfg.sampling.segments[-1].end_point
        expected_cols = self.cfg.channel_num.total + 2
        if self.cfg.data_type == DataType.ASCII:
            content = self.from_ascii_file(expected_rows, expected_cols)
        else:
            content = self.from_binary_file(expected_rows)
        return self._process_data(content, expected_rows, expected_cols)

    def read_from_memory(self) -> pd.DataFrame | None:
        expected_rows = self.cfg.sampling.segments[-1].end_point
        expected_cols = self.cfg.channel_num.total + 2
        if self.cfg.data_type == DataType.ASCII:
            content = self.from_ascii_str(expected_rows, expected_cols)
        else:
            content = self.from_binary_bytes(expected_rows)
        return self._process_data(content, expected_rows, expected_cols)

    def _process_data(self, content: pd.DataFrame | None, expected_rows: int,
                      expected_cols: int) -> pd.DataFrame | None:
        if content is None:
            return None

        type_mapping = {i: "int32" for i in range(2)}
        type_mapping.update({i + 2: "float64" for i in range(self.cfg.channel_num.analog)})
        type_mapping.update({
            self.cfg.channel_num.analog + 2 + i: "int32"
            for i in range(self.cfg.channel_num.status)
        })
        content = content.astype(type_mapping)

        analog_count = self.cfg.channel_num.analog
        if analog_count > 0:
            analog_list = list(self.cfg.analogs.values())
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            cols = list(range(2, 2 + analog_count))
            content.iloc[:, cols] = content.iloc[:, cols] * multipliers + offsets

        return content

    def from_ascii_file(self, expected_rows, expected_cols):
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
        return self._process_ascii_content(content, expected_rows, expected_cols, str(self.file_name))

    def from_ascii_str(self, expected_rows, expected_cols):
        if self.dat_text is None:
            return None

        try:
            from io import StringIO
            content = pd.read_csv(
                    StringIO(self.dat_text),
                    sep=",",
                    na_values=["", "NA", "null", "NULL", "None", "-", "NaN"],
                    keep_default_na=False,
                    header=None,
            )
            content = content.fillna(0)
        except Exception as e:
            raise ValueError(f"读取ASCII数据失败:{str(e)}")
        return self._process_ascii_content(content, expected_rows, expected_cols, "memory")

    def _process_ascii_content(self, content: pd.DataFrame, expected_rows: int, expected_cols: int, source_name: str):
        actual_rows, actual_cols = content.shape
        if actual_cols == expected_cols and actual_rows == expected_rows:
            return content

        if actual_rows != expected_rows:
            if actual_rows > expected_rows:
                try:
                    pd.isna(content.iloc[actual_rows, 0])
                    logging.warning(
                        f"数据{source_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},需要重新计算采样信息")
                except:
                    logging.warning(
                        f"数据{source_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},数据类型错误进行剪切")
                content = content.iloc[:expected_rows, :]

        if actual_cols != expected_cols:
            digital_cols = actual_cols - self.cfg.channel_num.analog - 2
            if digital_cols < 0:
                logging.error(
                    f"数据{source_name}数据拆分错误，期望最少读取{self.cfg.channel_num.analog + 2}列，实际读取{actual_cols}列，不符合返回空数据！")
                return None
            else:
                logging.error(
                    f"数据{source_name}数据拆分错误，期望读取{self.cfg.channel_num.total + 2}列，实际读取{actual_cols}列，丢弃数字量数据！")
                content = content.iloc[:, : self.cfg.channel_num.analog + 2]
                new_columns = [self.cfg.channel_num.analog + 2 + i for i in range(self.cfg.channel_num.status)]
                new_data = pd.DataFrame(0, index=content.index, columns=new_columns)
                content = pd.concat([content, new_data], axis=1)
        return content

    def from_binary_file(self, expected_rows):
        try:
            binary_data = self.file_name.read_bytes()
        except Exception as e:
            logging.error(f"读取{self.file_name}文件中的二进制数据失败: {e}")
            return None
        return self._process_binary_data(binary_data, expected_rows, str(self.file_name))

    def from_binary_bytes(self, expected_rows):
        if self.dat_bytes is None:
            return None
        return self._process_binary_data(self.dat_bytes, expected_rows, "memory")

    def _process_binary_data(self, binary_data: bytes, expected_rows: int, source_name: str):
        data_size = len(binary_data)
        digital_word_count = (self.cfg.channel_num.status + 15) // 16
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        is_int32 = self.cfg.data_type in INT32_TYPES
        analog_dtype_str = "i4" if is_int32 else "i2"
        analog_count = self.cfg.channel_num.analog
        dt = np.dtype([
            ("index", "<i4", 1),
            ("timestamp", "<i4", 1),
            ("analog", "<" + analog_dtype_str, analog_count),
            ("status", "<u2", digital_word_count),
        ])
        item_size = dt.itemsize
        sample_count = data_size // item_size

        if sample_count == expected_rows:
            samples = np.frombuffer(binary_data, dtype=dt)
        else:
            logging.warning(
                f"期望采样点数量：{expected_rows},数据不是{item_size}的整数倍，实际读取{sample_count}个采样点")
            samples = np.frombuffer(binary_data, dtype=dt, count=sample_count)

        index_data = samples["index"].astype(np.int32)
        timestamp_data = samples["timestamp"].astype(np.int32)
        analog_data = samples["analog"].astype(np.float64)

        if self.cfg.channel_num.status > 0:
            digital_data = samples["status"].reshape(-1, digital_word_count)
            digital_bytes = digital_data.view(np.uint8).reshape(sample_count, -1)
            bits = np.unpackbits(digital_bytes, axis=1, bitorder="little")
            digital_bits = bits[:, : self.cfg.channel_num.status]
        else:
            digital_bits = np.zeros((sample_count, 0), dtype=np.int32)

        if self.cfg.channel_num.analog > 0:
            data_array = np.column_stack([index_data, timestamp_data, analog_data, digital_bits])
        else:
            data_array = np.column_stack([index_data, timestamp_data, digital_bits])

        content = pd.DataFrame(data_array)
        return content

    def write_file(self, output_file_path: ComtradeFile | Path | str, data_type: str = "BINARY"):
        output_file_path = ComtradeFile.from_path(output_file_path)
        data_path = output_file_path.dat_path.path

        if data_type.upper() == "ASCII":
            self._write_ascii_dat_file(data_path)
        else:
            self._write_binary_dat_file(data_path)
        return True

    def _write_ascii_dat_file(self, output_file_path: Path | str):
        self.data.to_csv(str(output_file_path), header=False, index=False)
        logging.info(f"数据文件{output_file_path}写入成功")

    def _write_binary_dat_file(self, output_file_path: Path | str):
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        is_int32 = self.cfg.data_type in INT32_TYPES
        analog_fmt = "<i" if is_int32 else "<h"

        analog_count = self.cfg.channel_num.analog
        digital_count = self.cfg.channel_num.status
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
                        ival = int(float(val.real) if hasattr(val, "real") else float(val))
                    else:
                        ival = 0
                    f.write(struct.pack(analog_fmt, ival))

                for word_idx in range(digital_word_count):
                    digital_word = 0
                    for bit_idx in range(16):
                        channel_idx = word_idx * 16 + bit_idx
                        col = 2 + analog_count + channel_idx
                        if channel_idx < digital_count and col < self.data.shape[1]:
                            bit_val = int(float(self.data.iloc[i, col].real) if hasattr(self.data.iloc[i, col],
                                                                                        "real") else float(
                                    self.data.iloc[i, col]))
                            if bit_val != 0:
                                digital_word |= 1 << bit_idx
                    f.write(struct.pack("<H", digital_word))
        logging.info(f"数据文件{output_file_path}写入成功")
        return True

    def verify_and_recalculate_sampling(self) -> Sampling:
        if self.data is None or len(self.data) < 2:
            return self.cfg.sampling

        timestamps_us = self.data.iloc[:, 1].to_numpy() * self.cfg.timemult
        time_diffs_us = np.diff(timestamps_us)

        change_indices = np.where(np.diff(time_diffs_us) != 0)[0] + 1
        segment_starts = np.concatenate([[0], change_indices])
        segment_ends = np.concatenate([change_indices, [len(timestamps_us)]])

        frequency = self.cfg.sampling.freq if self.cfg.sampling.freq else 50
        cycle_ms = 1000.0 / frequency

        segments = []
        for start, end in zip(segment_starts, segment_ends):
            if time_diffs_us[start] <= 0:
                continue

            samp = round(1_000_000.0 / time_diffs_us[start])
            start_point = start
            count = end - start
            cycle_point_num = samp / frequency

            segments.append(Segment(
                    samp=samp,
                    end_point=end,
                    start_point=start_point,
                    count=count,
                    cycle_point_num=cycle_point_num
            ))

        if not segments:
            return self.cfg.sampling

        self.cfg.sampling.segments = segments
        return self.cfg.sampling