#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from comtrade_io.model.configure import Configure
from comtrade_io.model.description.sampling import Sampling, Segment
from comtrade_io.model.comtrade_file import ComtradeFile
from comtrade_io.model.type import DataType
from comtrade_io.utils import get_logger

logger = get_logger()

CYCLE_TIME_MS = 20.0


class DataContent(BaseModel):
    """COMTRADE 数据文件解析器

    负责解析和写入 DAT 数据文件（ASCII 和二进制格式），数据列结构为：
    [点号, 时间戳, 模拟量通道1..N, 数字量通道1..M]

    数据来源支持三种方式：
    - 从文件路径读取（file_name 参数传入 .dat 文件）
    - 从内存 ASCII 文本解析（dat_text 参数传入）
    - 从内存二进制数据解析（dat_bytes 参数传入）

    ASCII 格式每行一个采样点，逗号分隔；二进制格式每个采样点固定帧长。
    解析后自动根据 CFG 配置中的 multiplier/offset 对模拟量进行物理值转换。
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    cfg: Configure | None = Field(default=None, description="配置文件")
    file_name: Path | ComtradeFile | str | None = Field(
        default=None, description="dat文件路径"
    )
    dat_text: str | None = Field(default=None, description="DAT数据文本(ASCII格式)")
    dat_bytes: bytes | None = Field(default=None, description="DAT数据字节(二进制格式)")
    data: pd.DataFrame | None = Field(default=None, description="数据内容")

    def model_post_init(self, context: Any):
        if self.cfg is None:
            return
        if self.file_name is not None:
            cf = ComtradeFile.from_path(file_path=self.file_name)
            if not cf.dat_path.is_enabled():
                return
            self.file_name = cf.dat_path.path
            logger.info(f"开始解析数据文件: {self.file_name}")
            self.data = self.read()
            self._post_read()
        elif self.dat_text is not None or self.dat_bytes is not None:
            logger.info("开始解析内存数据")
            expected_rows = (
                self.cfg.sampling.segments[-1].end_point
                if self.cfg.sampling.segments
                else 0
            )
            expected_cols = self.cfg.channel_num.total + 2
            if self.cfg.data_type == DataType.ASCII and self.dat_text is not None:
                content = self.from_ascii_str(expected_rows, expected_cols)
            elif self.dat_bytes is not None:
                content = self._process_binary_data(
                    self.dat_bytes, expected_rows, "memory"
                )
            else:
                return
            self.data = self._process_data(content, expected_rows, expected_cols)
            self._post_read()

    def get_data(
        self,
        index: int,
        data_type: str = "analog",
        start_point: int = 1,
        end_point: int = None,
    ):
        """获取指定通道的录波数据片段

        参数:
            index: 通道索引（从 0 开始）
            data_type: 数据类型，可选 "point" / "time" / "analog" / "status"
            start_point: 起始采样点（从 1 开始）
            end_point: 结束采样点（不含）

        返回:
            numpy.ndarray | None: 指定通道的数据数组
        """
        if self.data is None:
            return None

        data_type = data_type.lower()
        col_index_map = {
            "point": 0,
            "time": 1,
            "analog": 2,
            "status": self.cfg.channel_num.analog + 2,
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
        if (
            start_point < 0
            or start_point >= end_point
            or end_point > self.data.shape[0]
        ):
            return None
        if 0 <= col_index < self.data.shape[1]:
            return self.data.iloc[start_point:end_point, col_index].to_numpy()

        return None

    def read(self) -> pd.DataFrame | None:
        """从文件读取 DAT 数据

        根据 cfg.data_type 自动选择 ASCII 或二进制解析路径。

        返回:
            pd.DataFrame | None: 解析后的数据帧，列结构为 [点号, 时间, 模拟量..., 数字量...]
        """
        if self.cfg is None:
            return None
        expected_rows = (
            self.cfg.sampling.segments[-1].end_point
            if self.cfg.sampling.segments
            else 0
        )
        expected_cols = self.cfg.channel_num.total + 2
        format_name = self.cfg.data_type.value
        logger.debug(
            f"期望数据: {expected_rows}行 x {expected_cols}列, 格式: {format_name}"
        )
        if self.cfg.data_type == DataType.ASCII:
            content = self.from_ascii_file(expected_rows, expected_cols)
        else:
            content = self.from_binary_file(expected_rows)
        result = self._process_data(content, expected_rows, expected_cols)
        if result is not None:
            logger.info(f"数据解析完成: {result.shape[0]}行 x {result.shape[1]}列")
        return result

    def _process_data(
        self, content: pd.DataFrame | None, expected_rows: int, expected_cols: int
    ) -> pd.DataFrame | None:
        """处理原始解析数据，进行数据类型转换和模拟量物理值换算

        对解析后的 DataFrame 进行后处理：
        1. 调整列数匹配 CFG 配置（处理列数不匹配的情况）
        2. 设置数据类型（点号/时间为 int32，模拟量为 float64，数字量为 int32）
        3. 根据 multiplier 和 offset 将模拟量原始值转换为物理值

        参数:
            content: 原始解析数据
            expected_rows: 期望行数
            expected_cols: 期望列数

        返回:
            pd.DataFrame | None: 处理后的数据帧
        """
        if content is None:
            return None

        actual_cols = content.shape[1]
        analog_count = min(self.cfg.channel_num.analog, actual_cols - 2)
        status_start = 2 + analog_count
        status_count = (
            min(self.cfg.channel_num.status, actual_cols - status_start)
            if status_start < actual_cols
            else 0
        )

        type_mapping = {i: "int32" for i in range(min(2, actual_cols))}
        type_mapping.update({i + 2: "float64" for i in range(analog_count)})
        if status_count > 0:
            type_mapping.update(
                {status_start + i: "int32" for i in range(status_count)}
            )
        content = content.astype(type_mapping)

        if analog_count > 0:
            analog_list = list(self.cfg.analogs.values())[:analog_count]
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            cols = list(range(2, 2 + analog_count))
            content.iloc[:, cols] = content.iloc[:, cols] * multipliers + offsets
            logger.debug(f"模拟量转换完成: {analog_count}个通道")

        return content

    def _post_read(self):
        """数据读取完成后的校验和采样信息修正

        当实际数据点数与 CFG 配置文件不一致时发出警告，
        并触发采样段重算以修正采样信息。
        """
        if (
            self.data is not None
            and self.cfg.sampling.segments
            and self.data.shape[0] != self.cfg.sampling.segments[-1].end_point
        ):
            logger.warning(
                f"实际读取数据点：{self.data.shape[0]}与配置文件数据点{self.cfg.sampling.segments[-1].end_point}不一致，根据采样点时间进行修正"
            )
        self.verify_and_recalculate_sampling()

    def from_ascii_file(self, expected_rows, expected_cols):
        """从 ASCII 格式的 DAT 文件读取数据

        使用 pandas.read_csv 读取逗号分隔的文本文件。

        参数:
            expected_rows: 期望行数
            expected_cols: 期望列数

        返回:
            pd.DataFrame | None: 原始数据帧（未做类型转换和物理值换算）
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
            logger.debug(f"ASCII数据文件读取完成: {self.file_name}")
        except Exception as e:
            raise ValueError(f"读取数据文件失败:{str(e)}")
        return self._process_ascii_content(
            content, expected_rows, expected_cols, str(self.file_name)
        )

    def from_ascii_str(self, expected_rows, expected_cols):
        """从内存中的 ASCII 文本解析 DAT 数据

        参数:
            expected_rows: 期望行数
            expected_cols: 期望列数

        返回:
            pd.DataFrame | None: 原始数据帧
        """
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
        return self._process_ascii_content(
            content, expected_rows, expected_cols, "memory"
        )

    def _process_ascii_content(
        self,
        content: pd.DataFrame,
        expected_rows: int,
        expected_cols: int,
        source_name: str,
    ):
        """校验并修正 ASCII 格式数据的行列数

        当实际行列数与期望值不一致时进行容错处理：
        - 行数过多：截断至期望行数
        - 列数不足：丢弃数据并填充默认值
        - 列数过多：丢弃多余列

        参数:
            content: 原始数据帧
            expected_rows: 期望行数
            expected_cols: 期望列数
            source_name: 数据来源（文件路径或 "memory"）

        返回:
            pd.DataFrame | None: 行列修正后的数据帧
        """
        actual_rows, actual_cols = content.shape
        if actual_cols == expected_cols and actual_rows == expected_rows:
            return content

        if actual_rows != expected_rows:
            if actual_rows > expected_rows:
                try:
                    pd.isna(content.iloc[actual_rows, 0])
                    logger.warning(
                        f"数据{source_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},需要重新计算采样信息"
                    )
                except Exception:
                    logger.warning(
                        f"数据{source_name}中实际采样点{actual_rows}超过配置文件中定义采样点{expected_rows},数据类型错误进行剪切"
                    )
                content = content.iloc[:expected_rows, :]

        if actual_cols != expected_cols:
            digital_cols = actual_cols - self.cfg.channel_num.analog - 2
            if digital_cols < 0:
                logger.error(
                    f"数据{source_name}数据拆分错误，期望最少读取{self.cfg.channel_num.analog + 2}列，实际读取{actual_cols}列，不符合返回空数据！"
                )
                return None
            else:
                logger.error(
                    f"数据{source_name}数据拆分错误，期望读取{self.cfg.channel_num.total + 2}列，实际读取{actual_cols}列，丢弃数字量数据！"
                )
                content = content.iloc[:, : self.cfg.channel_num.analog + 2]
                new_columns = [
                    self.cfg.channel_num.analog + 2 + i
                    for i in range(self.cfg.channel_num.status)
                ]
                new_data = pd.DataFrame(0, index=content.index, columns=new_columns)
                content = pd.concat([content, new_data], axis=1)
        return content

    def from_binary_file(self, expected_rows):
        """从二进制格式的 DAT 文件读取数据

        支持 BINARY（int16 模拟量）和 BINARY32/FLOAT32（int32 模拟量）格式。

        参数:
            expected_rows: 期望采样点数

        返回:
            pd.DataFrame | None: 解析后的数据帧
        """
        try:
            binary_data = self.file_name.read_bytes()
        except Exception as e:
            logger.error(f"读取{self.file_name}文件中的二进制数据失败: {e}")
            return None
        return self._process_binary_data(
            binary_data, expected_rows, str(self.file_name)
        )

    def _process_binary_data(
        self, binary_data: bytes, expected_rows: int, source_name: str
    ):
        """解析二进制 DAT 数据为 DataFrame

        二进制格式帧结构（小端序）：
        - index: int32 (4字节) — 采样点号
        - timestamp: int32 (4字节) — 时间戳
        - analogs: int16 或 int32 (N*2 或 N*4字节) — N个模拟量通道
        - status: uint16 (M*2字节) — M个状态字（每字16位，位宽展平为独立通道）

        BINARY 格式模拟量为 int16，BINARY32/FLOAT32 格式为 int32。
        数字量通道数向上取整到 16 的倍数作为状态字数量。

        参数:
            binary_data: 二进制数据字节
            expected_rows: 期望采样点数
            source_name: 数据来源（文件路径或 "memory"）

        返回:
            pd.DataFrame: 解析后的数据帧，列结构为 [点号, 时间, 模拟量..., 数字量...]
        """
        data_size = len(binary_data)
        status_word_count = (self.cfg.channel_num.status + 15) // 16
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        is_int32 = self.cfg.data_type in INT32_TYPES
        analog_dtype_str = "i4" if is_int32 else "i2"
        analog_count = self.cfg.channel_num.analog
        dt = np.dtype(
            [
                ("index", "<i4", 1),
                ("timestamp", "<i4", 1),
                ("analog", "<" + analog_dtype_str, analog_count),
                ("status", "<u2", status_word_count),
            ]
        )
        item_size = dt.itemsize
        sample_count = data_size // item_size

        logger.debug(
            f"二进制数据格式: {self.cfg.data_type.value}, "
            f"模拟量={analog_count}个({analog_dtype_str}), "
            f"状态字={status_word_count}个(u2)"
        )

        if sample_count == expected_rows:
            samples = np.frombuffer(binary_data, dtype=dt)
        else:
            logger.warning(
                f"期望采样点数量：{expected_rows},数据不是{item_size}的整数倍，实际读取{sample_count}个采样点"
            )
            samples = np.frombuffer(binary_data, dtype=dt, count=sample_count)

        index_data = samples["index"].astype(np.int32)
        timestamp_data = samples["timestamp"].astype(np.int32)
        analog_data = samples["analog"].astype(np.float64)

        if self.cfg.channel_num.status > 0:
            status_data = samples["status"].reshape(-1, status_word_count)
            status_bytes = status_data.view(np.uint8).reshape(sample_count, -1)
            bits = np.unpackbits(status_bytes, axis=1, bitorder="little")
            status_bits = bits[:, : self.cfg.channel_num.status]
        else:
            status_bits = np.zeros((sample_count, 0), dtype=np.int32)

        if self.cfg.channel_num.analog > 0:
            data_array = np.column_stack(
                [index_data, timestamp_data, analog_data, status_bits]
            )
        else:
            data_array = np.column_stack([index_data, timestamp_data, status_bits])

        content = pd.DataFrame(data_array)
        logger.debug(f"二进制数据解析完成: {sample_count}个采样点")
        return content

    def write_file(
        self,
        output_file_path: ComtradeFile | Path | str,
        data_type: str | DataType = "BINARY",
    ):
        """将数据写入 DAT 文件

        参数:
            output_file_path: 输出文件路径
            data_type: 数据格式 (ASCII / BINARY / BINARY32 / FLOAT32)

        返回:
            bool: 写入成功返回 True
        """
        output_file_path = ComtradeFile.from_path(output_file_path)
        data_path = output_file_path.dat_path.path

        if isinstance(data_type, DataType):
            dt_value = data_type
        else:
            dt_value = DataType.from_value(data_type.upper())

        logger.info(f"开始写入数据文件: {data_path}, 格式: {dt_value.value}")

        if dt_value == DataType.ASCII:
            self._write_ascii_dat_file(data_path)
        else:
            self._write_binary_dat_file(data_path, dt_value)
        return True

    def _write_ascii_dat_file(self, output_file_path: Path | str):
        """将数据写入 ASCII 格式的 DAT 文件

        每行一个采样点，逗号分隔各字段。

        参数:
            output_file_path: 输出文件路径
        """
        self.data.to_csv(str(output_file_path), header=False, index=False)
        logger.info(f"数据文件{output_file_path}写入成功")

    def _write_binary_dat_file(
        self, output_file_path: Path | str, data_type: DataType = DataType.BINARY
    ):
        """将数据写入二进制格式的 DAT 文件

        使用 numpy 向量化写入，帧结构为 [int32点号, int32时间戳, 模拟量..., 状态字...]。
        模拟量写入前先根据 multiplier/offset 反算原始值（物理值 → 原始值转换）。

        参数:
            output_file_path: 输出文件路径
            data_type: 二进制格式 (BINARY / BINARY32 / FLOAT32)
        """
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        is_int32 = data_type in INT32_TYPES
        analog_dtype = np.dtype(np.int32) if is_int32 else np.dtype(np.int16)

        analog_count = self.cfg.channel_num.analog
        status_count = self.cfg.channel_num.status
        status_word_count = (status_count + 15) // 16
        n = len(self.data)

        logger.debug(
            f"写入二进制数据: {n}个采样点, "
            f"模拟量格式={'i4' if is_int32 else 'i2'}, 状态字={status_word_count}个"
        )

        fields = [("index", "<i4"), ("timestamp", "<i4")]
        if analog_count > 0:
            fields.append(("analog", analog_dtype.str, analog_count))
        if status_word_count > 0:
            fields.append(("status", "<u2", status_word_count))

        dt = np.dtype(fields)
        records = np.zeros(n, dtype=dt)

        records["index"] = np.round(self.data.iloc[:, 0].to_numpy()).astype(np.int32)
        records["timestamp"] = np.round(self.data.iloc[:, 1].to_numpy()).astype(
            np.int32
        )

        if analog_count > 0:
            analog_list = list(self.cfg.analogs.values())[:analog_count]
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            analog_values = self.data.iloc[:, 2 : 2 + analog_count].to_numpy(
                dtype=np.float64
            )
            mask = multipliers != 0
            raw_values = np.zeros_like(analog_values)
            raw_values[:, mask] = (
                analog_values[:, mask] - offsets[mask]
            ) / multipliers[mask]
            records["analog"] = np.round(raw_values).astype(analog_dtype)

        if status_word_count > 0:
            status_bits = np.round(
                self.data.iloc[
                    :, 2 + analog_count : 2 + analog_count + status_count
                ].to_numpy()
            ).astype(np.uint16)
            packed = np.zeros((n, status_word_count), dtype=np.uint16)
            for w in range(status_word_count):
                start = w * 16
                n_bits = min(16, status_count - start)
                bits = status_bits[:, start : start + n_bits]
                weights = 1 << np.arange(n_bits, dtype=np.uint16)
                packed[:, w] = bits.dot(weights)
            records["status"] = packed

        records.tofile(str(output_file_path))
        logger.info(f"数据文件{output_file_path}写入成功")
        return True

    def verify_and_recalculate_sampling(self) -> Sampling:
        """根据实际时间戳校验并重算采样段信息

        通过分析时间戳差值的变化点来重新划分采样段，
        适用于实际数据点数与配置文件不一致或采样率发生变化的场景。

        返回:
            Sampling: 修正后的采样信息
        """
        if self.data is None or len(self.data) < 2:
            return self.cfg.sampling

        timestamps_us = self.data.iloc[:, 1].to_numpy() * self.cfg.timemult
        time_diffs_us = np.diff(timestamps_us)

        change_indices = np.where(np.diff(time_diffs_us) != 0)[0] + 1
        segment_starts = np.concatenate([[0], change_indices])
        segment_ends = np.concatenate([change_indices, [len(timestamps_us)]])

        frequency = self.cfg.sampling.freq if self.cfg.sampling.freq else 50

        segments = []
        for start, end in zip(segment_starts, segment_ends):
            if time_diffs_us[start] <= 0 or not np.isfinite(time_diffs_us[start]):
                continue

            samp = int(np.ceil(1_000_000.0 / time_diffs_us[start]))
            start_point = start
            count = end - start
            cycle_point_num = samp / frequency

            segments.append(
                Segment(
                    samp=samp,
                    end_point=end,
                    start_point=start_point,
                    count=count,
                    cycle_point_num=cycle_point_num,
                )
            )

        if not segments:
            return self.cfg.sampling

        orig_count = len(self.cfg.sampling.segments)
        self.cfg.sampling.segments = segments
        logger.info(
            f"采样段重算完成: {len(segments)}段 (原{orig_count}段), "
            f"采样率={segments[0].samp}Hz"
        )
        return self.cfg.sampling
