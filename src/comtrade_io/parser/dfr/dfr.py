"""DFR 文件编排器（主入口）。"""

import struct
from datetime import datetime
from pathlib import Path
from typing import Union

import pandas as pd
from pydantic import BaseModel, Field

from ...model.configure import Configure
from .binary_section import BinarySection
from .constants import DATA_MARKER, WNDR_TEXT_SIZE
from .converter import wndr_to_configure
from .wndr_section import WndrSection
from ...utils import get_logger

logger = get_logger()


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
    frame_data = raw[bin_start:]

    try:
        bs = BinarySection.from_raw(raw)
        bin_header = bs.bin_header
        frame_data = bs.frame_data
    except (ValueError, OSError, struct.error) as e:
        logger.warning(f"解析二进制头失败: {e}")
        bin_header = b""

    return DfrSection(cfg_text=cfg_text, dat_bytes=frame_data, bin_header=bin_header)


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
            wndr = WndrSection.from_text(self.sections.cfg_text)
            file_mtime = datetime.fromtimestamp(self.file_path.stat().st_mtime)
            return wndr_to_configure(wndr, file_mtime)
        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"解析 DFR 配置失败: {e}")
            return None

    def to_data_content(self, cfg: Configure) -> pd.DataFrame | None:
        if not self.sections.dat_bytes:
            logger.error("DFR 文件中未找到数据部分")
            return None
        try:
            raw = self.file_path.read_bytes()
            bs = BinarySection.from_raw(raw)
            return bs.to_dataframe(cfg)
        except (ValueError, OSError, TypeError) as e:
            logger.error(f"解析 DFR 数据失败: {e}")
            return None

    @classmethod
    def from_file(cls, file_path: str | Path) -> "DfrFile":
        return cls(file_path)
