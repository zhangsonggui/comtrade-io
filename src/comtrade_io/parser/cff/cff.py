from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

import pandas as pd

from ...model.configure import Configure
from .cfg_section import CfgSection
from .dat_section import DatSection
from .inf_section import InfSection
from .section_splitter import CffSection, extract_sections
from ...utils import get_logger

logger = get_logger()


@dataclass
class CffFile:
    sections: CffSection = field(default_factory=CffSection)
    file_path: Path | None = field(default=None)

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "CffFile":
        path = Path(file_path)
        return cls(sections=extract_sections(path), file_path=path)

    @property
    def cfg_text(self) -> str | None:
        return self.sections.cfg

    @property
    def dat_text(self) -> str | None:
        return self.sections.dat

    @property
    def inf_text(self) -> str | None:
        return self.sections.inf

    @property
    def hdr_text(self) -> str | None:
        return self.sections.hdr

    def to_configure(self) -> Configure | None:
        if not self.sections.cfg:
            logger.error("CFF 文件中未找到 CFG 配置部分")
            return None
        return CfgSection.from_str(self.sections.cfg)

    def to_data_content(self, config: Configure) -> pd.DataFrame | None:
        if not self.sections.dat and not self.sections.dat_bytes:
            logger.error("CFF 文件中未找到 DAT 数据部分")
            return None

        if config.description.data_type.value == "ASCII":
            return DatSection.from_str(config, self.sections.dat)
        else:
            return DatSection.from_bytes(config, self.sections.dat_bytes)

    def to_information(self):
        if not self.sections.inf:
            logger.debug("CFF 文件中未找到 INF 信息部分")
            return None
        return InfSection.from_str(self.sections.inf)
