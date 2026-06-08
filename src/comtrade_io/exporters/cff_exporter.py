#!/usr/bin/env python
# -*- coding: utf-8 -*-
from io import BytesIO, StringIO
from pathlib import Path
from typing import TYPE_CHECKING

from comtrade_io.parser.dat import DatFile
from comtrade_io.utils import get_logger

if TYPE_CHECKING:
    from comtrade_io.model.comtrade import Comtrade

logger = get_logger()


def export_cff(
    comtrade: "Comtrade", output_path: "str | Path", data_format: str, **kwargs
) -> bool:
    from comtrade_io.exporters import _resolve_export_path

    cff_path = _resolve_export_path(output_path, ".cff")
    sections = ["--- file type CFG ---", str(comtrade.to_cfg())]

    inf_content = comtrade.to_inf()
    if inf_content:
        sections.append("--- file type INF ---")
        sections.append(inf_content)

    text_parts = "\n".join(sections)
    if data_format == "ASCII":
        buffer = StringIO()
        comtrade.data.to_csv(buffer, header=False, index=False)
        with open(cff_path, "w", encoding="gbk", errors="ignore") as f:
            f.write(text_parts + "\n")
            f.write("--- file type DAT ---\n")
            f.write(buffer.getvalue())
    else:
        buf = BytesIO()
        DatFile(comtrade.config).write(buf, comtrade.data, data_type=data_format)
        dat_bytes = buf.getvalue()
        with open(cff_path, "wb") as f:
            f.write((text_parts + "\n").encode("gbk", errors="ignore"))
            f.write("--- file type DAT ---\n".encode("gbk", errors="ignore"))
            f.write(dat_bytes)

    logger.info(f"CFF文件{cff_path}写入成功")
    return True
