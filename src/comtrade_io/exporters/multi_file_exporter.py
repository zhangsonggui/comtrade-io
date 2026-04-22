#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import TYPE_CHECKING

from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.utils import get_logger

if TYPE_CHECKING:
    from comtrade_io.comtrade import Comtrade

logging = get_logger()


def export_multi_file(comtrade: "Comtrade", output_path: "str | Path | ComtradeFile",
                      data_format: str, **kwargs) -> str:
    """导出多文件格式

    参数:
        comtrade: Comtrade对象
        output_path: 输出路径
        data_format: 数据格式 (ASCII/BINARY/BINARY32/FLOAT32)
        **kwargs: 其他参数

    返回:
        成功消息
    """
    cf = ComtradeFile.from_path(output_path)
    comtrade.write_cfg(str(cf.cfg_path.path))
    comtrade.dat.write_file(cf, data_type=data_format)
    if cf.inf_path.path:
        comtrade.write_inf(str(cf.inf_path.path))
    if cf.dmf_path.path:
        comtrade.write_dmf(str(cf.dmf_path.path))
    return f"文件保存成功: cfg={cf.cfg_path.path}, dat={cf.dat_path.path}"
