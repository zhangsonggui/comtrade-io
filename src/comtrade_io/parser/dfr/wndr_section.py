"""WNDR 文本头部解析模块。"""

import csv
import io

from pydantic import BaseModel, Field

from .constants import (
    DEFAULT_FULL_SCALE,
    DEFAULT_SAMPLES_PER_CYCLE,
)
from ...utils import get_logger, parse_float

logger = get_logger()


def _parse_csv_line(raw_line: str) -> list[str]:
    reader = csv.reader(io.StringIO(raw_line))
    try:
        return next(reader)
    except StopIteration:
        return []


class WndrAnalogChannel(BaseModel):
    idx: int = Field(description="通道索引")
    name: str = Field(default="", description="通道名称（如 Ia-N1）")
    phase_code: str = Field(default="", description="相别代码（с/в/а = A/B/C）")
    circuit: str = Field(default="", description="监测回路（А/С/Н = 高/中/低压侧）")
    full_scale: float = Field(default=0.0, description="满度值")
    conv_factor: float = Field(default=0.0, description="转换系数 a")
    unit_str: str = Field(default="", description="单位字符串（如 I-N1、ВН-U）")
    phase: str = Field(default="", description="标准相别字母")
    ch_type: int = Field(default=0, description="通道类型（1=电流，100=电压）")
    rated_primary: float = Field(default=0.0, description="一次额定值")

    @classmethod
    def from_wndr_line(cls, wndr_line: str) -> "WndrAnalogChannel":
        fields = _parse_csv_line(wndr_line)
        if len(fields) < 8:
            logger.warning(f"模拟通道行字段不足，跳过: {wndr_line}")
            return None

        idx = int(fields[0]) if fields[0].strip().isdigit() else 0
        name = fields[1].strip().strip('"')
        phase_code = fields[2].strip() if len(fields) > 2 else ""
        circuit = fields[3].strip() if len(fields) > 3 else ""
        full_scale = parse_float(fields[4]) if len(fields) > 4 else 0.0
        conv_factor = parse_float(fields[5]) if len(fields) > 5 else 0.0
        unit_str = fields[6].strip().strip('"') if len(fields) > 6 else ""
        phase = fields[7].strip() if len(fields) > 7 else ""
        ch_type = (
            int(fields[12]) if len(fields) > 12 and fields[12].strip().isdigit() else 0
        )
        rated_primary = parse_float(fields[13]) if len(fields) > 13 else 0.0

        return cls(
            idx=idx,
            name=name,
            phase_code=phase_code,
            circuit=circuit,
            full_scale=full_scale,
            conv_factor=conv_factor,
            unit_str=unit_str,
            phase=phase,
            ch_type=ch_type,
            rated_primary=rated_primary,
        )


class WndrStatusChannel(BaseModel):
    idx: int = Field(description="装置原始编号")
    name: str = Field(default="", description="通道名称")

    @classmethod
    def from_wndr_line(cls, wndr_line: str, seq: int) -> "WndrStatusChannel":
        fields = _parse_csv_line(wndr_line)
        raw_idx = int(fields[0]) if fields[0].strip().isdigit() else seq
        name = fields[1].strip().strip('"') if len(fields) > 1 else ""
        return cls(idx=raw_idx, name=name)


class WndrSection(BaseModel):
    station_name: str = Field(default="Unknown", description="变电站名称")
    total_channels: int = Field(default=0)
    analog_count: int = Field(default=0)
    status_count: int = Field(default=0)
    analog_channels: list[WndrAnalogChannel] = Field(default_factory=list)
    status_channels: list[WndrStatusChannel] = Field(default_factory=list)
    full_scale: int = Field(default=DEFAULT_FULL_SCALE)
    samples_per_cycle: int = Field(default=DEFAULT_SAMPLES_PER_CYCLE)
    total_samples: int = Field(default=0)
    grid_freq: float = Field(default=50.0)

    @classmethod
    def from_text(cls, text: str) -> "WndrSection":
        if not text or not text.strip():
            raise ValueError("WNDR 文本为空")

        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            raise ValueError("WNDR 文本为空")

        if lines[0] != "[WNDR]":
            logger.warning(f"WNDR 魔数缺失，期望 [WNDR]，实际 {lines[0]}")

        station_name = (
            cls._parse_station_name(lines[1]) if len(lines) > 1 else "Unknown"
        )

        ch_parts = lines[2].split(",") if len(lines) > 2 else ["0"]
        total = int(ch_parts[0]) if ch_parts[0].strip().isdigit() else 0
        analog_count = cls._extract_count(ch_parts[1]) if len(ch_parts) > 1 else 0
        status_count = cls._extract_count(ch_parts[2]) if len(ch_parts) > 2 else 0

        analog_channels = []
        status_channels = []
        cursor = 3

        for _ in range(analog_count):
            if cursor < len(lines):
                ch = WndrAnalogChannel.from_wndr_line(lines[cursor])
                if ch is not None:
                    analog_channels.append(ch)
                cursor += 1

        for seq in range(1, status_count + 1):
            if cursor < len(lines):
                ch = WndrStatusChannel.from_wndr_line(lines[cursor], seq)
                status_channels.append(ch)
                cursor += 1

        full_scale = DEFAULT_FULL_SCALE
        samples_per_cycle = DEFAULT_SAMPLES_PER_CYCLE
        total_samples = 0

        if cursor < len(lines):
            try:
                full_scale = int(lines[cursor])
            except (ValueError, TypeError):
                pass
            cursor += 1

        if cursor < len(lines):
            try:
                samples_per_cycle = int(lines[cursor])
            except (ValueError, TypeError):
                pass
            cursor += 1

        if cursor < len(lines):
            try:
                total_samples = int(lines[cursor])
            except (ValueError, TypeError):
                pass

        grid_freq = 50.0

        return cls(
            station_name=station_name,
            total_channels=total,
            analog_count=len(analog_channels),
            status_count=len(status_channels),
            analog_channels=analog_channels,
            status_channels=status_channels,
            full_scale=full_scale,
            samples_per_cycle=samples_per_cycle,
            total_samples=total_samples,
            grid_freq=grid_freq,
        )

    @classmethod
    def _parse_station_name(cls, line: str) -> str:
        fields = _parse_csv_line(line)
        raw = fields[0].strip('" ') if fields else "Unknown"
        return raw.split(",")[0] if "," in raw else raw

    @staticmethod
    def _extract_count(s: str) -> int:
        digits = "".join(c for c in s if c.isdigit())
        return int(digits) if digits else 0
