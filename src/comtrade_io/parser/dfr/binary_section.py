#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""DFR [Data] 二进制数据解析模块。"""

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from comtrade_io.model.configure import Configure
from comtrade_io.parser.dfr.constants import (
    ANALOG_WORDS,
    DATA_MARKER,
    DEFAULT_HEADER_SIZE,
    FRAME_SIZE,
    KNOWN_DEVICES,
    STATUS_WORDS,
    WNDR_TEXT_SIZE,
)
from comtrade_io.utils import get_logger

logger = get_logger()


def _device_header_size(device_id: str) -> int:
    info = KNOWN_DEVICES.get(device_id)
    if info is not None:
        return info["header_size"]
    logger.warning(f"未知设备 ID: {device_id}，使用默认头部大小 {DEFAULT_HEADER_SIZE}")
    return DEFAULT_HEADER_SIZE


class BinarySection(BaseModel):
    device_id: str = Field(default="", description="设备标识（如 2704V042）")
    bin_header: bytes = Field(default=b"", description="设备二进制头部")
    frame_data: bytes = Field(default=b"", description="采样帧数据")
    footer: bytes | None = Field(default=None, description="尾部数据")

    @classmethod
    def from_raw(cls, raw: bytes) -> "BinarySection":
        data_start = raw.find(DATA_MARKER)
        if data_start == -1:
            logger.warning("未找到 [Data] 标记，尝试从偏移 4088 处直接读取")
            data_start = WNDR_TEXT_SIZE

        off = data_start + len(DATA_MARKER)

        # 读取设备 ID：紧跟 [Data]\r\n，仅由 ASCII 字母/数字组成
        id_bytes = bytearray()
        for b in raw[off : off + 32]:
            if 48 <= b <= 57 or 65 <= b <= 90 or 97 <= b <= 122:  # 0-9, A-Z, a-z
                id_bytes.append(b)
            else:
                break
        device_id = id_bytes.decode("ascii")

        hdr_start = off + len(device_id)
        header_size = _device_header_size(device_id)

        bin_header = raw[hdr_start : hdr_start + header_size]
        frame_start = hdr_start + header_size
        frame_data = raw[frame_start:]

        return cls(
            device_id=device_id,
            bin_header=bin_header,
            frame_data=frame_data,
        )

    def to_dataframe(self, cfg: Configure) -> pd.DataFrame:
        raw = self.frame_data
        raw_size = len(raw) // FRAME_SIZE * FRAME_SIZE
        if raw_size == 0:
            return pd.DataFrame()

        frame_count = raw_size // FRAME_SIZE

        # 使用配置中的总采样点数（如果小于实际帧数则截断）
        if (
            cfg.description.sampling.segments
            and cfg.description.sampling.segments[0].end_point < frame_count
            and cfg.description.sampling.segments[0].end_point > 0
        ):
            frame_count = cfg.description.sampling.segments[0].end_point
            raw_size = frame_count * FRAME_SIZE

        analog_count = cfg.description.channel_num.analog
        status_count = cfg.description.channel_num.status
        status_word_count = max((status_count + 15) // 16, STATUS_WORDS)

        words_per_frame = FRAME_SIZE // 2
        frames = np.frombuffer(raw[:raw_size], dtype=np.int16).reshape(
            -1, words_per_frame
        )

        if frames.shape[1] < ANALOG_WORDS:
            raise ValueError(
                f"帧大小异常，期望 {ANALOG_WORDS} 个16位字，实际 {frames.shape[1]}"
            )

        analog_data = frames[:, :ANALOG_WORDS].astype(np.float64)
        status_data = frames[:, ANALOG_WORDS : ANALOG_WORDS + STATUS_WORDS].astype(
            np.uint16
        )

        # 转换为物理瞬时值：val = raw * multiplier + offset
        if analog_count > 0:
            analog_list = list(cfg.analogs.values())[:analog_count]
            multipliers = np.array([a.multiplier for a in analog_list])
            offsets = np.array([a.offset for a in analog_list])
            analog_data[:, :analog_count] = (
                analog_data[:, :analog_count] * multipliers + offsets
            )

        index_data = np.arange(1, frame_count + 1, dtype=np.int32)

        sampling_rate = 1200
        if cfg.description.sampling.segments:
            sampling_rate = cfg.description.sampling.segments[0].samp
        time_step = int(1_000_000 / sampling_rate) if sampling_rate > 0 else 833
        timestamp_data = (index_data - 1) * time_step
        timestamp_data = timestamp_data.astype(np.int32)

        rows = []
        for s in range(frame_count):
            row = [int(index_data[s]), int(timestamp_data[s])]
            row.extend(float(analog_data[s, a]) for a in range(analog_count))
            rows.append(row)

        df = pd.DataFrame(rows)

        if status_count > 0:
            bits_list = []
            for s in range(frame_count):
                status_bits = []
                for w in range(status_word_count):
                    word_val = int(status_data[s, w])
                    for b in range(16):
                        if len(status_bits) < status_count:
                            status_bits.append((word_val >> b) & 1)
                bits_list.append(status_bits)
            bits_array = np.array(bits_list, dtype=np.int32)
            bits_df = pd.DataFrame(bits_array)
            df = pd.concat(
                [df.reset_index(drop=True), bits_df.reset_index(drop=True)],
                axis=1,
                ignore_index=True,
            )

        df.columns = range(df.shape[1])
        return df
