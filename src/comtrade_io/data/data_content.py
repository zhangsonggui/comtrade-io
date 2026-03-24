#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
import struct
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from comtrade_io.cfg import Configure
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.type import DataType
from comtrade_io.utils import get_logger

logging = get_logger()


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

    # ------------------------------------------------------------------ #
    # In-memory constructor (used by CFF reader)                          #
    # ------------------------------------------------------------------ #

    @classmethod
    def from_str(
        cls,
        cfg: Configure,
        dat_str: Optional[str] = None,
        dat_bytes: Optional[bytes] = None,
    ) -> "DataContent":
        """
        Construct a DataContent directly from in-memory DAT content,
        bypassing the filesystem entirely.

        This is the CFF analogue of the normal constructor: instead of
        pointing at a file on disk, we hand the raw content straight to
        the same parsing methods that the file-based path uses.

        Exactly one of dat_str or dat_bytes must be provided:
          - dat_str   → ASCII encoding
          - dat_bytes → BINARY / BINARY32 / FLOAT32 encoding

        参数:
            cfg:       Already-parsed Configure for this record.
            dat_str:   Raw ASCII DAT content as a string.
            dat_bytes: Raw binary DAT content as bytes.
        """
        if dat_str is None and dat_bytes is None:
            raise ValueError("Either dat_str or dat_bytes must be provided.")
        if dat_str is not None and dat_bytes is not None:
            raise ValueError("Provide either dat_str or dat_bytes, not both.")

        # Build a minimal instance without triggering model_post_init's file
        # resolution logic.  We pass a sentinel path that intentionally does
        # not exist so that model_post_init returns early, then we set .data
        # ourselves via the appropriate parser.
        instance = cls.model_construct(
            cfg=cfg,
            file_name=Path("__cff_in_memory__"),
            data=None,
        )

        expected_rows = cfg.sampling.nrates[-1].end_point
        expected_cols = cfg.channel_num.total + 2

        if dat_str is not None:
            instance.data = instance._parse_ascii_str(dat_str, expected_rows, expected_cols)
        else:
            instance.data = instance._parse_binary_bytes(dat_bytes, expected_rows)

        instance.data = instance._apply_type_mapping_and_scaling(instance.data)
        return instance

    # ------------------------------------------------------------------ #
    # Public instance API (unchanged from original)                       #
    # ------------------------------------------------------------------ #

    def get_data(
            self,
            index: int,
            data_type: str = "analog",
            start_point: int = 1,
            end_point: int = None,
    ):
        """
        获取指定通道的数据
        """
        if self.data is None:
            return None

        data_type = data_type.lower()
        col_index_map = {
            "point": 0,
            "time": 1,
            "analog": 2,
            "digital": self.cfg.channel_num.analog + 2
        }
        base_col = col_index_map.get(data_type, 2)
        if data_type in ("analog", "digital"):
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
        """
        读取数据文件,返回数据对象(pandas.DataFrame)
        """
        expected_rows = self.cfg.sampling.nrates[-1].end_point
        expected_cols = self.cfg.channel_num.total + 2
        if self.cfg.data_type == DataType.ASCII:
            content = self.from_ascii_file(expected_rows, expected_cols)
        else:
            content = self.from_binary_file(expected_rows)
        return self._apply_type_mapping_and_scaling(content)

    # ------------------------------------------------------------------ #
    # Internal parsers — shared between file-based and in-memory paths    #
    # ------------------------------------------------------------------ #

    def _apply_type_mapping_and_scaling(self, content: pd.DataFrame) -> pd.DataFrame | None:
        """Apply dtype casting and analog channel scaling to a raw DataFrame."""
        if content is None:
            return None
        type_mapping = {i: "int32" for i in range(2)}
        type_mapping.update({i + 2: "float64" for i in range(self.cfg.channel_num.analog)})
        type_mapping.update({
            self.cfg.channel_num.analog + 2 + i: "int32"
            for i in range(self.cfg.channel_num.digital)
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

    def _parse_ascii_str(self, dat_str: str, expected_rows: int, expected_cols: int) -> pd.DataFrame | None:
        """
        Parse ASCII DAT content from a string.

        Mirrors from_ascii_file() but reads from a StringIO instead of a file
        path — same logic, different front door.
        """
        try:
            content = pd.read_csv(
                io.StringIO(dat_str),
                sep=",",
                na_values=["", "NA", "null", "NULL", "None", "-", "NaN"],
                keep_default_na=False,
                header=None,
            )
            content = content.fillna(0)
        except Exception as e:
            raise ValueError(f"Failed to parse ASCII DAT content: {e}")

        actual_rows, actual_cols = content.shape
        if actual_cols == expected_cols and actual_rows == expected_rows:
            return content
        if actual_rows > expected_rows:
            try:
                pd.isna(content.iloc[actual_rows, 0])
                logging.warning(f"CFF DAT: actual rows {actual_rows} > expected {expected_rows}")
            except Exception:
                logging.warning(f"CFF DAT: truncating {actual_rows} rows to {expected_rows}")
                content = content.iloc[:expected_rows, :]
        if actual_cols != expected_cols:
            digital_cols = actual_cols - self.cfg.channel_num.analog - 2
            if digital_cols < 0:
                logging.error(f"CFF DAT: too few columns ({actual_cols}), expected at least "
                              f"{self.cfg.channel_num.analog + 2}")
                return None
            else:
                logging.warning(f"CFF DAT: column mismatch ({actual_cols} vs {expected_cols}), "
                                f"padding digital channels with zeros")
                content = content.iloc[:, : self.cfg.channel_num.analog + 2]
                new_columns = [self.cfg.channel_num.analog + 2 + i
                               for i in range(self.cfg.channel_num.digital)]
                new_data = pd.DataFrame(0, index=content.index, columns=new_columns)
                content = pd.concat([content, new_data], axis=1)
        return content

    def _parse_binary_bytes(self, dat_bytes: bytes, expected_rows: int) -> pd.DataFrame | None:
        """
        Parse binary DAT content from a bytes object.

        Mirrors from_binary_file() but accepts raw bytes instead of a Path —
        same numpy dtype layout, different data source.
        """
        digital_word_count = (self.cfg.channel_num.digital + 15) // 16
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        analog_dtype = np.int32 if self.cfg.data_type in INT32_TYPES else np.int16
        dt = np.dtype([
            ("index",     np.int32,     1),
            ("timestamp", np.int32,     1),
            ("analog",    analog_dtype, self.cfg.channel_num.analog),
            ("digital",   np.uint16,    digital_word_count),
        ])
        item_size = dt.itemsize
        sample_count = len(dat_bytes) // item_size

        if sample_count != expected_rows:
            logging.warning(f"CFF DAT: expected {expected_rows} samples, got {sample_count}")

        samples = np.frombuffer(dat_bytes, dtype=dt, count=sample_count)

        index_data     = samples["index"].astype(np.int32)
        timestamp_data = samples["timestamp"].astype(np.int32)
        analog_data    = samples["analog"].astype(np.float64)

        if self.cfg.channel_num.digital > 0:
            digital_data  = samples["digital"].reshape(-1, digital_word_count)
            digital_bytes = digital_data.view(np.uint8).reshape(sample_count, -1)
            bits          = np.unpackbits(digital_bytes, axis=1, bitorder="little")
            digital_bits  = bits[:, : self.cfg.channel_num.digital]
        else:
            digital_bits = np.zeros((sample_count, 0), dtype=np.int32)

        if self.cfg.channel_num.analog > 0:
            data_array = np.column_stack([index_data, timestamp_data, analog_data, digital_bits])
        else:
            data_array = np.column_stack([index_data, timestamp_data, digital_bits])

        return pd.DataFrame(data_array)

    # ------------------------------------------------------------------ #
    # File-based parsers (original implementations, unchanged)            #
    # ------------------------------------------------------------------ #

    def from_ascii_file(self, expected_rows, expected_cols):
        """读取ASCII格式的数据文件"""
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
        if actual_cols == expected_cols and actual_rows == expected_rows:
            return content
        if actual_rows != expected_rows:
            if actual_rows > expected_rows:
                try:
                    pd.isna(content.iloc[actual_rows, 0])
                    logging.warning(
                        f"数据文件{self.file_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},需要重新计算采样信息"
                    )
                except Exception:
                    logging.warning(
                        f"数据文件{self.file_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},数据类型错误进行剪切"
                    )
                    content = content.iloc[:expected_rows, :]
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
        """读取BINARY格式的数据文件"""
        file_size = self.file_name.stat().st_size
        digital_word_count = (self.cfg.channel_num.digital + 15) // 16
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        analog_dtype = np.int32 if self.cfg.data_type in INT32_TYPES else np.int16
        dt = np.dtype([
            ("index",     np.int32,     1),
            ("timestamp", np.int32,     1),
            ("analog",    analog_dtype, self.cfg.channel_num.analog),
            ("digital",   np.uint16,    digital_word_count),
        ])
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

        index_data     = samples["index"].astype(np.int32)
        timestamp_data = samples["timestamp"].astype(np.int32)
        analog_data    = samples["analog"].astype(np.float64)

        if self.cfg.channel_num.digital > 0:
            digital_data  = samples["digital"].reshape(-1, digital_word_count)
            digital_bytes = digital_data.view(np.uint8).reshape(sample_count, -1)
            bits          = np.unpackbits(digital_bytes, axis=1, bitorder="little")
            digital_bits  = bits[:, : self.cfg.channel_num.digital]
        else:
            digital_bits = np.zeros((sample_count, 0), dtype=np.int32)

        if self.cfg.channel_num.analog > 0:
            data_array = np.column_stack([index_data, timestamp_data, analog_data, digital_bits])
        else:
            data_array = np.column_stack([index_data, timestamp_data, digital_bits])

        return pd.DataFrame(data_array)

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
        analog_int32 = self.cfg.data_type in {DataType.BINARY32, DataType.FLOAT32}
        analog_fmt = "<i" if analog_int32 else "<h"
        analog_count  = self.cfg.channel_num.analog
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
