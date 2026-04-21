#!/usr/bin/env python
# -*- coding: utf-8 -*-
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.type.data_type import DataType
from comtrade_io.utils import get_logger
from .cff_exporter import export_cff
from .csv_exporter import export_csv
from .json_exporter import export_json
from .multi_file_exporter import export_multi_file

logging = get_logger()


class ExportFormat(str, Enum):
    """导出格式枚举"""
    MULTI_FILE = "multi_file"
    CFF = "cff"
    JSON = "json"
    CSV = "csv"


def export_format(func: Callable) -> Callable:
    """
    导出格式装饰器 - 简洁版本

    使用字典映射替代if-else，根据格式参数分发到对应处理方法。
    """

    @wraps(func)
    def wrapper(self, output_path: str | Path | ComtradeFile,
                format: str = "multi_file",
                data_format: str = "BINARY",
                **kwargs) -> Any:
        # 验证并转换格式枚举
        try:
            export_fmt = ExportFormat(format.lower())
            data_fmt = DataType.from_value(data_format.upper())
        except ValueError as e:
            raise ValueError(f"无效格式参数: {e}") from e

        # 保存原始data_type
        original_data_type = self.cfg.data_type

        # 直接使用DataType枚举
        self.cfg.data_type = data_fmt

        try:
            # 使用字典映射分发
            export_handlers = {
                ExportFormat.MULTI_FILE: export_multi_file,
                ExportFormat.CFF       : export_cff,
                ExportFormat.JSON      : export_json,
                ExportFormat.CSV       : export_csv,
            }
            logging.debug(f"使用{export_fmt.value}格式导出")
            return export_handlers[export_fmt](self, output_path, data_fmt.value, **kwargs)
        finally:
            # 恢复原始data_type
            self.cfg.data_type = original_data_type

    return wrapper
