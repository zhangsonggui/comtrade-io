#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from comtrade_io.utils import get_logger

if TYPE_CHECKING:
    from comtrade_io.model.comtrade import Comtrade

logger = get_logger()


def export_csv(
    comtrade: "Comtrade", output_path: "str | Path", data_format: str, **kwargs
) -> bool:
    """导出CSV格式

    参数:
        comtrade: Comtrade对象
        output_path: 输出路径
        data_format: 数据格式 (忽略，仅为了接口统一)
        **kwargs: 其他参数 (include_headers: 是否包含表头，默认为True)

    返回:
        成功与否
    """
    from comtrade_io.exporters import _resolve_export_path

    path = _resolve_export_path(output_path, ".csv")

    headers = ['Point', 'Time']
    for idx in sorted(comtrade.analogs.keys()):
        a = comtrade.analogs[idx]
        headers.append(f"{a.name or f'A{idx}'}")
    for idx in sorted(comtrade.statuses.keys()):
        s = comtrade.statuses[idx]
        headers.append(f"{s.name or f'D{idx}'}")

    comtrade.data.to_csv(
        path,
        header=headers if kwargs.get("include_headers", True) else False,
        index=False,
    )
    logger.info(f"CSV文件{path}写入成功")
    return True
