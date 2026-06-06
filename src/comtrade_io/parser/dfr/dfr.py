import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from comtrade_io.model.configure import Configure
from comtrade_io.model.description import PrecisionTime
from comtrade_io.parser.cfg.cfg import CfgFile
from comtrade_io.utils import get_logger

logger = get_logger()

WNDR_TEXT_SIZE = 4088
DATA_MARKER = b"[Data]\r\n"
BIN_HEADER_SIZE = 49
FRAME_SIZE = 72
ANALOG_WORDS = 32
STATUS_WORDS = 4

CYRILLIC_TO_LATIN = str.maketrans(
    {
        "\u0410": "A",  # Cyrillic А → Latin A (ampere)
        "\u043a": "k",  # Cyrillic к → Latin k
        "\u0412": "V",  # Cyrillic В → Latin V (volt)
        "\u043e": "o",  # Cyrillic о → Latin o
        "\u0435": "e",  # Cyrillic е → Latin e
    }
)


class DfrSection(BaseModel):
    cfg_text: str | None = Field(default=None, description="WNDR 配置部分文本")
    dat_bytes: bytes | None = Field(default=None, description="二进制数据部分")
    bin_header: bytes | None = Field(default=None, description="二进制头")


def extract_sections(dfr_path: Union[str, Path]) -> DfrSection:
    path = Path(dfr_path)
    if not path.exists():
        raise FileNotFoundError(f"DFR 文件不存在: {dfr_path}")

    raw = path.read_bytes()

    text = raw[:WNDR_TEXT_SIZE]
    try:
        cfg_text = text.decode("cp1251")
    except UnicodeDecodeError:
        cfg_text = text.decode("cp1251", errors="replace")

    data_start = raw.find(DATA_MARKER)
    if data_start == -1:
        logger.warning("未找到 [Data] 标记，尝试从偏移 4088 处直接读取")
        data_start = WNDR_TEXT_SIZE

    bin_start = data_start + len(DATA_MARKER)
    bin_header = raw[bin_start : bin_start + BIN_HEADER_SIZE]
    frame_data = raw[bin_start + BIN_HEADER_SIZE :]

    result = DfrSection(cfg_text=cfg_text, dat_bytes=frame_data, bin_header=bin_header)
    return result


def _parse_wndr_analog_fields(raw_line: str) -> list[str]:
    reader = csv.reader(io.StringIO(raw_line))
    return next(reader)


def wndr_to_cfg(wndr_text: str, file_mtime: datetime | None = None) -> str:
    lines = [l.strip() for l in wndr_text.split("\n") if l.strip()]
    if not lines:
        raise ValueError("WNDR 文本为空")

    if lines[0] != "[WNDR]":
        logger.warning(f"WNDR 魔数缺失，期望 [WNDR]，实际 {lines[0]}")

    line2 = lines[1]
    line2_fields = _parse_wndr_analog_fields(line2)
    station_name_raw = line2_fields[0].strip('"') if line2_fields else "Unknown"
    station_name = (
        station_name_raw.split(",")[0] if "," in station_name_raw else station_name_raw
    )

    ch_num_line = lines[2]
    ch_parts = ch_num_line.split(",")
    total = int(ch_parts[0])

    def _extract_count(s):
        digits = "".join(c for c in s if c.isdigit())
        return int(digits) if digits else 0

    analog_count = _extract_count(ch_parts[1]) if len(ch_parts) > 1 else 0
    status_count = _extract_count(ch_parts[2]) if len(ch_parts) > 2 else 0

    analog_lines = []
    status_lines = []
    cursor = 3
    for i in range(analog_count):
        analog_lines.append(lines[cursor])
        cursor += 1
    for i in range(status_count):
        status_lines.append(lines[cursor])
        cursor += 1

    cfg_lines = []
    cfg_lines.append(f"{station_name},DFR,1999")

    cfg_lines.append(f"{total},{analog_count}A,{status_count}D")

    cyr_unit_map = {
        "\u0410": "A",
        "\u043a\u0412": "kV",
        "\u043e.\u0435.": "pu",
    }

    for wndr_line in analog_lines:
        fields = _parse_wndr_analog_fields(wndr_line)
        if len(fields) < 8:
            logger.warning(f"模拟通道行格式异常，跳过: {wndr_line}")
            continue

        idx = fields[0].strip()
        name = fields[1].strip() if len(fields) > 1 else ""
        unit_raw = fields[3].strip() if len(fields) > 3 else ""
        unit_conv = unit_raw.translate(CYRILLIC_TO_LATIN)
        scale_val = fields[4].strip() if len(fields) > 4 else "1.0"
        offset_val = fields[5].strip() if len(fields) > 5 else "0.0"
        equip = fields[6].strip() if len(fields) > 6 else ""
        phase = fields[7].strip() if len(fields) > 7 else ""

        sec = fields[12].strip() if len(fields) > 12 else "1"
        prim = fields[13].strip() if len(fields) > 13 else "1"
        if not sec:
            sec = "1"
        if not prim:
            prim = "1"

        cfg_line = f"{idx},{name},{phase},{equip},{unit_conv},{scale_val},{offset_val},0,0,0,{prim},{sec},S"
        cfg_lines.append(cfg_line)

    for seq_idx, wndr_line in enumerate(status_lines, 1):
        fields = _parse_wndr_analog_fields(wndr_line)
        name = fields[1].strip() if len(fields) > 1 else ""
        cfg_lines.append(f"{seq_idx},{name}")

    full_scale = int(lines[cursor]) if cursor < len(lines) else 32768
    cursor += 1
    samples_per_cycle = int(lines[cursor]) if cursor < len(lines) else 24
    cursor += 1

    sampling_rate = samples_per_cycle * 50  # 50Hz grid

    cfg_lines.append("50")
    cfg_lines.append("1")
    cfg_lines.append(f"{sampling_rate},{lines[cursor]}")

    file_time = PrecisionTime(time=file_mtime) if file_mtime else PrecisionTime()
    cfg_lines.append(file_time.__str__())
    cfg_lines.append(file_time.__str__())

    cfg_lines.append("BINARY")
    cfg_lines.append("1.0")

    return "\n".join(cfg_lines)


class DfrFile:
    file_path: Path
    sections: DfrSection

    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.sections = extract_sections(self.file_path)

    @property
    def cfg_text(self) -> str | None:
        return self.sections.cfg_text

    def to_configure(self) -> Configure | None:
        if not self.sections.cfg_text:
            logger.error("DFR 文件中未找到配置部分")
            return None
        try:
            file_mtime = datetime.fromtimestamp(self.file_path.stat().st_mtime)
            cfg_text = wndr_to_cfg(self.sections.cfg_text, file_mtime)
            return CfgFile.from_str(cfg_text)
        except Exception as e:
            logger.error(f"解析 DFR 配置失败: {e}")
            return None

    def to_data_content(self, cfg: Configure) -> pd.DataFrame | None:
        if not self.sections.dat_bytes:
            logger.error("DFR 文件中未找到数据部分")
            return None
        try:
            return self._parse_binary_data(cfg)
        except Exception as e:
            logger.error(f"解析 DFR 数据失败: {e}")
            return None

    def _parse_binary_data(self, cfg: Configure) -> pd.DataFrame:
        raw = self.sections.dat_bytes
        frame_count = len(raw) // FRAME_SIZE

        if cfg.description.sampling.segments:
            cfg.description.sampling.segments[0].end_point = frame_count

        analog_count = cfg.description.channel_num.analog
        status_count = cfg.description.channel_num.status
        status_word_count = (status_count + 15) // 16
        if status_word_count < STATUS_WORDS:
            status_word_count = STATUS_WORDS

        analogs = np.frombuffer(raw, dtype=np.int16).reshape(-1, FRAME_SIZE // 2)
        if analogs.shape[1] < ANALOG_WORDS:
            raise ValueError(
                f"帧大小异常，期望 {ANALOG_WORDS} 个字，实际 {analogs.shape[1]}"
            )
        analog_data = analogs[:, :ANALOG_WORDS].astype(np.float64)

        status_data = analogs[:, ANALOG_WORDS : ANALOG_WORDS + STATUS_WORDS].astype(
            np.uint16
        )

        index_data = np.arange(1, frame_count + 1, dtype=np.int32)

        timemult = cfg.description.timemult if cfg.description.timemult else 1.0
        timestamp_data = (index_data - 1) * 833
        timestamp_data = timestamp_data.astype(np.int32)

        rows = []
        for s in range(frame_count):
            row = [index_data[s], timestamp_data[s]]
            row.extend(float(analog_data[s, a]) for a in range(analog_count))
            rows.append(row)

        df = pd.DataFrame(rows)

        if status_count > 0:
            bits_list = []
            for s in range(frame_count):
                status_bits = []
                for w in range(status_word_count):
                    word_val = status_data[s, w]
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

    @classmethod
    def from_file(cls, file_path: str | Path) -> "DfrFile":
        return cls(file_path)
