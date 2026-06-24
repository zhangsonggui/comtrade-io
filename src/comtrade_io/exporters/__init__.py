from pathlib import Path
from typing import TYPE_CHECKING

from .cff_exporter import export_cff
from .csv_exporter import export_csv
from .decorators import ExportFormat, export_format
from .json_exporter import export_json, save_json
from .multi_file_exporter import export_multi_file
from ..model.type.data_type import DataType

if TYPE_CHECKING:
    from ..parser.comtrade_file import ComtradeFile

__all__ = [
    "export_format", "ExportFormat", "DataType",
    "export_multi_file", "export_cff", "export_json", "save_json", "export_csv"
]


def _resolve_export_path(output_path: "str | Path | ComtradeFile", suffix: str) -> Path:
    from ..parser.comtrade_file import ComtradeFile

    if isinstance(output_path, ComtradeFile):
        if output_path.cfg_path.path:
            return output_path.cfg_path.path.with_suffix(suffix)
        raise ValueError(f"无法确定后缀为{suffix}的输出路径")
    path = Path(output_path)
    return path if path.suffix.lower() == suffix else path.with_suffix(suffix)
