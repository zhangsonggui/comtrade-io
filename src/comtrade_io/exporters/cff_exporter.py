#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from io import BytesIO, StringIO
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.utils import get_logger

if TYPE_CHECKING:
    from comtrade_io.comtrade import Comtrade

logging = get_logger()


def export_cff(comtrade: "Comtrade", output_path: "str | Path | ComtradeFile",
               data_format: str, **kwargs) -> str:
    """导出CFF单文件格式

    参数:
        comtrade: Comtrade对象
        output_path: 输出路径
        data_format: 数据格式 (ASCII/BINARY/BINARY32/FLOAT32)
        **kwargs: 其他参数

    返回:
        成功消息
    """
    cf = ComtradeFile.from_path(output_path)
    cff_path = cf.cff_path.path
    if not cff_path:
        base_path = cf.cfg_path.path or cf.dat_path.path
        if base_path:
            cff_path = base_path.parent / (base_path.stem + '.cff')
        else:
            raise ValueError("无法确定CFF输出路径")

    sections = []

    sections.append("--- file type CFG ---")
    sections.append(str(comtrade.cfg))

    inf_content = comtrade.to_inf()
    if inf_content:
        sections.append("--- file type INF ---")
        sections.append(inf_content)

    sections.append("--- file type DAT ---")
    if data_format == "ASCII":
        buffer = StringIO()
        comtrade.dat.data.to_csv(buffer, header=False, index=False)
        sections.append(buffer.getvalue())
    else:
        buffer = BytesIO()
        with NamedTemporaryFile(delete=False, suffix='.dat') as tmp:
            tmp_path = tmp.name
        try:
            tmp_cf = ComtradeFile.from_path(tmp_path)
            comtrade.dat.write_file(tmp_cf, data_type=data_format)
            dat_bytes = Path(tmp_path).read_bytes()
            sections.append(dat_bytes.decode('latin-1'))
        finally:
            os.unlink(tmp_path)
    with open(cff_path, 'w', encoding='gbk') as f:
        f.write('\n'.join(sections))

    logging.info(f"CFF文件{cff_path}写入成功")
    return f"文件保存成功: {cff_path}"
