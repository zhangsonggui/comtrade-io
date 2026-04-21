#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.utils import get_logger

if TYPE_CHECKING:
    from comtrade_io.comtrade import Comtrade

logging = get_logger()


def _to_json(data: dict, indent: int | None = None) -> str:
    """将字典转换为JSON字符串，处理特殊对象

    参数:
        data: 要序列化的字典
        indent: JSON缩进

    返回:
        JSON字符串
    """

    def convert(obj):
        if hasattr(obj, 'value'):
            return obj.value
        if isinstance(obj, UUID):
            return str(obj)
        if hasattr(obj, '__dict__'):
            return str(obj)
        return obj

    def process(d):
        if isinstance(d, dict):
            return {k: process(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [process(i) for i in d]
        else:
            return convert(d)

    data = process(data)
    return json.dumps(data, ensure_ascii=False, default=str, indent=indent)


def save_json(comtrade: "Comtrade", output_file_path: "Path | str",
              indent: int | None = None) -> bool:
    """将Comtrade对象保存为JSON文件（包含dat数据）

    参数:
        comtrade: Comtrade对象
        output_file_path: 输出文件路径
        indent: JSON缩进

    返回:
        成功与否
    """
    data = comtrade.model_dump(mode='python')
    data.pop("cfg", None)
    data.pop("file", None)

    if comtrade.dat is not None and comtrade.dat.data is not None:
        df = comtrade.dat.data
        analog_list = data.get("analogs", [])
        for ch in analog_list:
            if isinstance(ch, dict) and ch.get("index") is not None:
                col_idx = ch["index"] + 2
                if col_idx < df.shape[1]:
                    ch["data"] = df.iloc[:, col_idx].tolist()
        status_list = data.get("statuses", [])
        for ch in status_list:
            if isinstance(ch, dict) and ch.get("index") is not None:
                col_idx = comtrade.cfg.channel_num.analog + ch["index"] + 2
                if col_idx < df.shape[1]:
                    ch["data"] = df.iloc[:, col_idx].tolist()

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(_to_json(data, indent))
    logging.info(f"json数据写入{output_file_path}成功")
    return True


def export_json(comtrade: "Comtrade", output_path: "str | Path | ComtradeFile",
                data_format: str, **kwargs) -> bool:
    """导出JSON格式

    参数:
        comtrade: Comtrade对象
        output_path: 输出路径
        data_format: 数据格式 (忽略，仅为了接口统一)
        **kwargs: 其他参数 (indent: JSON缩进)

    返回:
        成功与否
    """
    path = Path(output_path) if not isinstance(output_path, ComtradeFile) else \
        (output_path.cfg_path.path.parent / (
                output_path.cfg_path.path.stem + '.json') if output_path.cfg_path.path else None)
    if not path:
        raise ValueError("无法确定JSON输出路径")
    if path.suffix.lower() != '.json':
        path = path.with_suffix('.json')

    # 调用save_json函数
    return save_json(comtrade, path, indent=kwargs.get('indent'))
