#!/usr/bin/env python
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from io import BytesIO, StringIO
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from comtrade_io.model.configure import Configure
from comtrade_io.model.description.sampling import Sampling, Segment
from comtrade_io.model.type import DataType
from comtrade_io.utils import get_logger

logger = get_logger()

CYCLE_TIME_MS = 20.0


@dataclass
class DatFile:
    config: Configure

    @classmethod
    def from_file(
        cls, config: Configure, file_name: str | Path
    ) -> Optional[pd.DataFrame]:
        path = Path(file_name)
        if not path.exists():
            logger.error(f"DAT文件不存在: {path}")
            return None

        logger.info(f"开始解析数据文件: {path}")
        raw_bytes = path.read_bytes()

        if config.description.data_type == DataType.ASCII:
            for enc in ("utf-8", "gbk", "latin-1"):
                try:
                    text = raw_bytes.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                text = raw_bytes.decode("utf-8", errors="replace")
            return cls.from_str(config, text)
        else:
            return cls.from_bytes(config, raw_bytes)

    @classmethod
    def from_str(cls, config: Configure, text: str) -> Optional[pd.DataFrame]:
        dat = cls(config=config)
        logger.info("开始解析ASCII内存数据")
        df = dat._parse_ascii(text)
        if df is None:
            return None
        df = dat._validate_shape(df)
        if df is not None:
            dat._post_process(df)
        return df

    @classmethod
    def from_bytes(cls, config: Configure, data: bytes) -> Optional[pd.DataFrame]:
        dat = cls(config=config)
        logger.info("开始解析二进制内存数据")
        df = dat._parse_binary(data)
        if df is None:
            return None
        df = dat._validate_shape(df)
        if df is not None:
            dat._post_process(df)
        return df

    def write(
        self,
        output_path: str | Path | BytesIO,
        data: pd.DataFrame,
        data_type: str | DataType = "BINARY",
    ) -> bool:
        if isinstance(output_path, BytesIO):
            buf = output_path
        else:
            buf = Path(output_path)
        if isinstance(data_type, DataType):
            dt_value = data_type
        else:
            dt_value = DataType.from_value(data_type.upper())

        logger.info(f"开始写入数据文件: {buf}, 格式: {dt_value.value}")

        if dt_value == DataType.ASCII:
            self._write_ascii(data, buf)
        else:
            self._write_binary(data, buf, dt_value)
        return True

    def _parse_ascii(self, text: str) -> Optional[pd.DataFrame]:
        try:
            content = pd.read_csv(
                StringIO(text),
                sep=",",
                na_values=["", "NA", "null", "NULL", "None", "-", "NaN"],
                keep_default_na=False,
                header=None,
            )
            content = content.fillna(0)
        except Exception as e:
            raise ValueError(f"读取ASCII数据失败: {e}")

        content = self._apply_type_mapping(content)
        return self._apply_analog_scaling(content)

    def _parse_binary(self, data: bytes) -> pd.DataFrame:
        config = self.config
        data_size = len(data)
        status_word_count = (config.description.channel_num.status + 15) // 16
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        is_int32 = config.description.data_type in INT32_TYPES
        analog_dtype_str = "i4" if is_int32 else "i2"
        analog_count = config.description.channel_num.analog

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

        expected_rows = (
            config.description.sampling.segments[-1].end_point
            if config.description.sampling.segments
            else 0
        )

        logger.debug(
            f"二进制数据格式: {config.description.data_type.value}, "
            f"模拟量={analog_count}个({analog_dtype_str}), "
            f"状态字={status_word_count}个(u2)"
        )

        if sample_count == expected_rows:
            samples = np.frombuffer(data, dtype=dt)
        else:
            logger.warning(
                f"期望采样点数量：{expected_rows}，数据不是{item_size}的整数倍，实际读取{sample_count}个采样点"
            )
            samples = np.frombuffer(data, dtype=dt, count=sample_count)

        index_data = samples["index"].astype(np.int32)
        timestamp_data = samples["timestamp"].astype(np.int32)
        analog_data = samples["analog"].astype(np.float64)

        if config.description.channel_num.status > 0:
            status_data = samples["status"].reshape(-1, status_word_count)
            status_bytes = status_data.view(np.uint8).reshape(sample_count, -1)
            bits = np.unpackbits(status_bytes, axis=1, bitorder="little")
            status_bits = bits[:, : config.description.channel_num.status]
        else:
            status_bits = np.zeros((sample_count, 0), dtype=np.int32)

        if config.description.channel_num.analog > 0:
            data_array = np.column_stack(
                [index_data, timestamp_data, analog_data, status_bits]
            )
        else:
            data_array = np.column_stack([index_data, timestamp_data, status_bits])

        content = pd.DataFrame(data_array)
        logger.debug(f"二进制数据解析完成: {sample_count}个采样点")
        return self._apply_analog_scaling(content)

    def _apply_type_mapping(self, content: pd.DataFrame) -> pd.DataFrame:
        config = self.config
        actual_cols = content.shape[1]
        analog_count = min(config.description.channel_num.analog, actual_cols - 2)
        status_start = 2 + analog_count
        status_count = (
            min(config.description.channel_num.status, actual_cols - status_start)
            if status_start < actual_cols
            else 0
        )

        type_mapping = {i: "int32" for i in range(min(2, actual_cols))}
        type_mapping.update({i + 2: "float64" for i in range(analog_count)})
        if status_count > 0:
            type_mapping.update(
                {status_start + i: "int32" for i in range(status_count)}
            )
        return content.astype(type_mapping)

    def _apply_analog_scaling(self, content: pd.DataFrame) -> pd.DataFrame:
        config = self.config
        analog_count = min(
            config.description.channel_num.analog, max(0, content.shape[1] - 2)
        )
        if analog_count > 0:
            analog_list = list(config.analogs.values())[:analog_count]
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            cols = list(range(2, 2 + analog_count))
            content.iloc[:, cols] = content.iloc[:, cols] * multipliers + offsets
            logger.debug(f"模拟量转换完成: {analog_count}个通道")
        return content

    def _validate_shape(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        config = self.config
        actual_rows, actual_cols = df.shape
        expected_cols = config.description.channel_num.total + 2
        expected_rows = (
            config.description.sampling.segments[-1].end_point
            if config.description.sampling.segments
            else 0
        )

        logger.info(
            f"数据形状校验: {actual_rows}行x{actual_cols}列 "
            f"(期望: {expected_rows}行x{expected_cols}列)"
        )

        if actual_cols == expected_cols and actual_rows == expected_rows:
            return df

        if actual_rows != expected_rows and actual_rows > expected_rows:
            logger.warning(
                f"实际采样点{actual_rows}超过配置定义{expected_rows}，进行剪切"
            )
            df = df.iloc[:expected_rows, :]

        if actual_cols != expected_cols:
            digital_cols = actual_cols - config.description.channel_num.analog - 2
            if digital_cols < 0:
                logger.error(
                    f"期望最少读取{config.description.channel_num.analog + 2}列，"
                    f"实际读取{actual_cols}列，返回空数据"
                )
                return None
            else:
                logger.error(
                    f"期望读取{config.description.channel_num.total + 2}列，"
                    f"实际读取{actual_cols}列，丢弃数字量数据"
                )
                df = df.iloc[:, : config.description.channel_num.analog + 2]
                new_columns = [
                    config.description.channel_num.analog + 2 + i
                    for i in range(config.description.channel_num.status)
                ]
                new_data = pd.DataFrame(0, index=df.index, columns=new_columns)
                df = pd.concat([df, new_data], axis=1)

        return df

    def _post_process(self, df: pd.DataFrame):
        config = self.config
        if df is None:
            return

        # 应用时标倍率因子
        timemult = config.description.timemult
        if timemult is not None and timemult != 1.0:
            df.iloc[:, 1] = df.iloc[:, 1] * timemult
            logger.debug(f"时标倍率因子 {timemult} 已应用到时间戳列")

        if (
            config.description.sampling.segments
            and df.shape[0] != config.description.sampling.segments[-1].end_point
        ):
            logger.warning(
                f"实际读取数据点：{df.shape[0]}与配置文件数据点"
                f"{config.description.sampling.segments[-1].end_point}不一致，"
                "根据采样点时间进行修正"
            )
        self._verify_and_recalculate_sampling(df)

    def _verify_and_recalculate_sampling(self, df: pd.DataFrame) -> Sampling:
        config = self.config
        if df is None or len(df) < 2:
            return config.description.sampling

        timestamps_us = df.iloc[:, 1].to_numpy() * config.description.timemult
        time_diffs_us = np.diff(timestamps_us)

        change_indices = np.where(np.diff(time_diffs_us) != 0)[0] + 1
        segment_starts = np.concatenate([[0], change_indices])
        segment_ends = np.concatenate([change_indices, [len(timestamps_us)]])

        frequency = (
            config.description.sampling.freq if config.description.sampling.freq else 50
        )

        segments = []
        for start, end in zip(segment_starts, segment_ends):
            if time_diffs_us[start] <= 0 or not np.isfinite(time_diffs_us[start]):
                continue

            n_intervals = end - start - 1
            if n_intervals > 0:
                avg_interval = (
                    timestamps_us[end - 1] - timestamps_us[start]
                ) / n_intervals
                samp = int(np.round(1_000_000.0 / avg_interval))
            else:
                samp = int(np.round(1_000_000.0 / time_diffs_us[start]))
            count = end - start
            cycle_point_num = samp / frequency

            segments.append(
                Segment(
                    samp=samp,
                    end_point=end,
                    start_point=start,
                    count=count,
                    cycle_point_num=cycle_point_num,
                )
            )

        if not segments:
            return config.description.sampling

        orig_count = len(config.description.sampling.segments)
        config.description.sampling.segments = segments
        logger.info(
            f"采样段重算完成: {len(segments)}段 (原{orig_count}段), "
            f"采样率={segments[0].samp}Hz"
        )
        return config.description.sampling

    def _write_ascii(self, data: pd.DataFrame, output: Path | BytesIO):
        config = self.config
        analog_count = config.description.channel_num.analog
        if analog_count > 0:
            analog_list = list(config.analogs.values())[:analog_count]
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            analog_values = data.iloc[:, 2 : 2 + analog_count].to_numpy(
                dtype=np.float64
            )
            mask = multipliers != 0
            raw_values = np.zeros_like(analog_values)
            raw_values[:, mask] = (
                analog_values[:, mask] - offsets[mask]
            ) / multipliers[mask]
            out = data.copy()
            out.iloc[:, 2 : 2 + analog_count] = np.round(raw_values)
        else:
            out = data

        if isinstance(output, BytesIO):
            out.to_csv(output, header=False, index=False)
        else:
            out.to_csv(str(output), header=False, index=False)
        logger.info(f"数据文件{output}写入成功")

    def _write_binary(
        self,
        data: pd.DataFrame,
        output: Path | BytesIO,
        data_type: DataType = DataType.BINARY,
    ):
        config = self.config
        INT32_TYPES = {DataType.BINARY32, DataType.FLOAT32}
        is_int32 = data_type in INT32_TYPES
        analog_dtype = np.dtype(np.int32) if is_int32 else np.dtype(np.int16)

        analog_count = config.description.channel_num.analog
        status_count = config.description.channel_num.status
        status_word_count = (status_count + 15) // 16
        n = len(data)

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

        records["index"] = np.round(data.iloc[:, 0].to_numpy()).astype(np.int32)
        records["timestamp"] = np.round(data.iloc[:, 1].to_numpy()).astype(np.int32)

        if analog_count > 0:
            analog_list = list(config.analogs.values())[:analog_count]
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            analog_values = data.iloc[:, 2 : 2 + analog_count].to_numpy(
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
                data.iloc[
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

        if isinstance(output, BytesIO):
            output.write(records.tobytes())
        else:
            records.tofile(str(output))
        logger.info(f"数据文件{output}写入成功")
