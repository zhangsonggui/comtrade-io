#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import TYPE_CHECKING

from comtrade_io.exporters.cff_exporter import export_cff
from comtrade_io.exporters.csv_exporter import export_csv
from comtrade_io.exporters.decorators import ExportFormat, export_format
from comtrade_io.exporters.json_exporter import export_json, save_json
from comtrade_io.exporters.multi_file_exporter import export_multi_file
from comtrade_io.model.type.data_type import DataType

if TYPE_CHECKING:
    from comtrade_io.parser.comtrade_file import ComtradeFile

__all__ = [
    "export_format", "ExportFormat", "DataType",
    "export_multi_file", "export_cff", "export_json", "save_json", "export_csv"
]


def _resolve_export_path(output_path: "str | Path | ComtradeFile", suffix: str) -> Path:
    from comtrade_io.parser.comtrade_file import ComtradeFile

    if isinstance(output_path, ComtradeFile):
        if output_path.cfg_path.path:
            return output_path.cfg_path.path.with_suffix(suffix)
        raise ValueError(f"无法确定后缀为{suffix}的输出路径")
    path = Path(output_path)
    return path if path.suffix.lower() == suffix else path.with_suffix(suffix)
