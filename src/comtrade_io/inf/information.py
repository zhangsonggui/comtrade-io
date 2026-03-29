#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.inf.bus_section import BusSection
from comtrade_io.inf.line_section import LineSection
from comtrade_io.inf.transformer_section import TransformerSection
from comtrade_io.utils import get_logger

logging = get_logger()


def parse_section_header(header_str: str):
    # 验证方括号格式
    bracket_match = re.match(r'^\[([^\]]+)\]$', header_str)
    if not bracket_match:
        return None

    content = bracket_match.group(1).strip()

    # 按空格分割，提取 area
    space_parts = content.split(' ', 1)
    if len(space_parts) < 2:
        return None

    area = space_parts[0]
    rest = space_parts[1]

    # 按 _# 分割 type 和 index
    hash_match = re.match(r'^(.+?)_#(\d+)$', rest)
    if hash_match:
        section_type = hash_match.group(1)
        index = int(hash_match.group(2))
    else:
        # 无法识别_#，整个作为type，index为0
        section_type = rest
        index = 0

    return {'area': area, 'type': section_type, 'index': index}


class Information(BaseModel):
    """INF文件解析和序列化主类"""
    bus_sections: Optional[list[BusSection]] = Field(default_factory=list, description="母线")
    line_sections: Optional[list[LineSection]] = Field(default_factory=list, description="线路")
    transformer_sections: Optional[list[TransformerSection]] = Field(default_factory=list, description="变压器")

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> 'Information|None':
        """从文件名中解析INF文件"""
        cf = ComtradeFile.from_path(file_name)
        if not cf.inf_path.is_enabled():
            return None
        inf_path = cf.inf_path.path
        logging.debug(f"开始解析INF文件: {inf_path}")
        try:
            inf_content = inf_path.read_text(encoding='gbk')
        except UnicodeDecodeError:
            logging.warning(f"配置文件{inf_path}编码不是GBK编码，尝试使用UTF8解析")
            try:
                inf_content = inf_path.read_text(encoding="utf-8", errors='replace')
            except UnicodeDecodeError:
                logging.error(f"无法解析INF文件: {inf_path}")
                return None
        return Information.from_str(inf_content)

    @classmethod
    def from_str(cls, content: str) -> 'Information|None':
        """从字符串解析INF内容"""
        _inf = cls()
        _current_section = {}
        for line in content.split('\n'):
            line = line.strip()
            # 跳过空行和注释行
            if not line or line.startswith(';'):
                continue
            # 检查是否是节标题 [xxx]
            if line.startswith('[') and ']' in line:
                # 保存前一个节
                if _current_section:
                    _type = _current_section.get('type')
                    if _type.upper() == 'BUS':
                        _inf.bus_sections.append(BusSection.from_dict(_current_section))
                    elif _type.upper() == 'LINE':
                        _inf.line_sections.append(LineSection.from_dict(_current_section))
                    elif _type.upper() == 'TRANSFORMER':
                        _inf.transformer_sections.append(TransformerSection.from_dict(_current_section))
                    _current_section = {}
                _current_section = parse_section_header(line)
                # 仅处理母线、线路、变压器
                if _current_section.get('type').upper() not in ['BUS', 'LINE', 'TRANSFORMER']:
                    _current_section = {}
                    continue
            elif _current_section and '=' in line:
                key, value = line.split('=', 1)
                _current_section[key.strip()] = value.strip()
        return _inf


if __name__ == '__main__':
    inf_file = r"D:\codeArea\Git_Work\comtrade\comtrade-io\example\data\20190413-023734.#0006BC1A.inf"
    inf = Information.from_file(inf_file)
    print(inf.model_dump())
