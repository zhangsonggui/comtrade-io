#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import TYPE_CHECKING

from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.utils import get_logger

if TYPE_CHECKING:
    from comtrade_io.comtrade import Comtrade

logging = get_logger()


def export_csv(comtrade: "Comtrade", output_path: "str | Path | ComtradeFile",
               data_format: str, **kwargs) -> bool:
    """导出CSV格式

    参数:
        comtrade: Comtrade对象
        output_path: 输出路径
        data_format: 数据格式 (忽略，仅为了接口统一)
        **kwargs: 其他参数 (include_headers: 是否包含表头，默认为True)

    返回:
        成功与否
    """
    path = Path(output_path) if not isinstance(output_path, ComtradeFile) else \
        (output_path.cfg_path.path.parent / (
                output_path.cfg_path.path.stem + '.csv') if output_path.cfg_path.path else None)
    if not path:
        raise ValueError("无法确定CSV输出路径")
    if path.suffix.lower() != '.csv':
        path = path.with_suffix('.csv')

    headers = ['Point', 'Time']
    for idx in sorted(comtrade.cfg.analogs.keys()):
        a = comtrade.cfg.analogs[idx]
        headers.append(f"{a.name or f'A{idx}'}")
    for idx in sorted(comtrade.cfg.statuses.keys()):
        s = comtrade.cfg.statuses[idx]
        headers.append(f"{s.name or f'D{idx}'}")

    comtrade.dat.data.to_csv(path, header=headers if kwargs.get('include_headers', True) else False, index=False)
    logging.info(f"CSV文件{path}写入成功")
    return True
