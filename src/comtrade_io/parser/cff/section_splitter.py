import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from comtrade_io.utils import get_logger

logger = get_logger()


@dataclass
class CffSection:
    cfg: str | None = field(default=None)
    dat: str | None = field(default=None)
    dat_bytes: bytes | None = field(default=None)
    inf: str | None = field(default=None)
    hdr: str | None = field(default=None)


def extract_sections(cff_path: Union[str, Path]) -> CffSection:
    path = Path(cff_path)
    if not path.exists():
        raise FileNotFoundError(f"CFF 文件不存在: {cff_path}")

    content_bytes = path.read_bytes()
    content = content_bytes.decode("gbk", errors="replace")

    section_pattern = re.compile(
        r"^--{1,2}\s*file\s+type\s*:?\s+(\w+)(?:\s+[^-]*)?\s*---",
        re.IGNORECASE | re.MULTILINE,
    )

    sections = {}
    matches = list(section_pattern.finditer(content))

    for i, match in enumerate(matches):
        section_type = match.group(1).upper()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[section_type] = (start, end)

    result = CffSection()
    for section_type, (start, end) in sections.items():
        section_content = content[start:end].strip()
        if section_type == "CFG":
            result.cfg = section_content
        elif section_type == "DAT":
            result.dat = section_content
            result.dat_bytes = content_bytes[start:end]
        elif section_type == "INF":
            result.inf = section_content
        elif section_type == "HDR":
            result.hdr = section_content

    return result
