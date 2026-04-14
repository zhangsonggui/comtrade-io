#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel, Field

from comtrade_io.cfg import Configure
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.data import DataContent
from comtrade_io.utils import get_logger

logging = get_logger()


class CffSection(BaseModel):
    """CFF文件分段数据类

    存储从CFF单文件中提取的各个部分的数据。

    属性:
        cfg: CFG 配置部分文本
        dat: DAT 数据部分文本(ASCII格式)
        dat_bytes: DAT 数据部分字节(二进制格式)
        inf: INF 信息部分文本
        hdr: HDR 头部部分文本
    """
    cfg: Optional[str] = Field(default=None, description="CFG 配置部分文本")
    dat: Optional[str] = Field(default=None, description="DAT 数据部分文本(ASCII格式)")
    dat_bytes: Optional[bytes] = Field(default=None, description="DAT 数据部分字节(二进制格式)")
    inf: Optional[str] = Field(default=None, description="INF 信息部分文本")
    hdr: Optional[str] = Field(default=None, description="HDR 头部部分文本")


def extract_sections(cff_path: Union[str, Path]) -> CffSection:
    """从 CFF 文件中提取各个 section

    CFF文件使用类似 "---file type CFG---" 的标记来分隔不同部分。

    参数:
        cff_path: CFF 文件路径

    返回:
        CffSection: 包含各部分文本的对象

    异常:
        FileNotFoundError: 当CFF文件不存在时抛出
    """
    path = Path(cff_path)
    if not path.exists():
        raise FileNotFoundError(f"CFF 文件不存在: {cff_path}")

    content = path.read_text(encoding="gbk", errors="replace")
    content_bytes = path.read_bytes()

    section_pattern = re.compile(r"^--{1,2}\s*file\s+type\s+(\w+)\s*---", re.IGNORECASE | re.MULTILINE)

    sections = {}
    matches = list(section_pattern.finditer(content))

    for i, match in enumerate(matches):
        section_type = match.group(1).upper()
        start = match.end()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(content)
        sections[section_type] = (start, end)

    result = CffSection()
    for section_type, (start, end) in sections.items():
        section_content = content[start:end].strip()
        if section_type == "CFG":
            result.cfg = section_content
        elif section_type == "DAT":
            result.dat = section_content
            result.dat_bytes = content_bytes[start:end]
        elif section_type == "INF":
            result.inf = section_content
        elif section_type == "HDR":
            result.hdr = section_content

    return result


class CffFile:
    """CFF 单文件格式解析器

    CFF 格式将 cfg/dat/inf/hdr 合并为单个 .cff 文件，便于文件管理和传输。

    属性:
        file_path: CFF文件路径
        sections: 提取的各部分数据
    """

    def __init__(self, file_path: Union[str, Path]):
        """初始化CffFile对象

        参数:
            file_path: CFF文件路径
        """
        self.file_path = Path(file_path)
        self.sections = extract_sections(self.file_path)

    @property
    def cfg_text(self) -> Optional[str]:
        """返回 CFG 配置部分文本

        返回:
            Optional[str]: CFG配置文本，不存在则返回None
        """
        return self.sections.cfg

    @property
    def dat_text(self) -> Optional[str]:
        """返回 DAT 数据部分文本

        返回:
            Optional[str]: DAT数据文本(ASCII格式)，不存在则返回None
        """
        return self.sections.dat

    @property
    def inf_text(self) -> Optional[str]:
        """返回 INF 信息部分文本

        返回:
            Optional[str]: INF信息文本，不存在则返回None
        """
        return self.sections.inf

    @property
    def hdr_text(self) -> Optional[str]:
        """返回 HDR 头部部分文本

        返回:
            Optional[str]: HDR头部文本，不存在则返回None
        """
        return self.sections.hdr

    def to_configure(self) -> Optional[Configure]:
        """将 CFG 部分转换为 Configure 对象

        返回:
            Optional[Configure]: 配置对象，解析失败返回None
        """
        if not self.cfg_text:
            logging.error("CFF 文件中未找到 CFG 配置部分")
            return None

        try:
            return Configure.from_str(self.cfg_text)
        except Exception as e:
            logging.error(f"解析 CFG 配置失败: {e}")
            return None

    def to_configure_from_file(self) -> Optional[Configure]:
        """将 CFG 部分写入临时文件并通过 Configure.from_file 解析

        返回:
            Optional[Configure]: 配置对象，解析失败返回None
        """
        if not self.cfg_text:
            logging.error("CFF 文件中未找到 CFG 配置部分")
            return None

        temp_dir = self.file_path.parent
        temp_cfg_path = temp_dir / "_temp_cff.cfg"

        try:
            temp_cfg_path.write_text(self.cfg_text, encoding="utf-8", errors="replace")
            return Configure.from_file(temp_cfg_path)
        except Exception as e:
            logging.error(f"解析 CFG 配置失败: {e}")
            return None
        finally:
            if temp_cfg_path.exists():
                temp_cfg_path.unlink()

    def to_data_content(self, cfg: Configure) -> Optional[DataContent]:
        """将 DAT 部分转换为 DataContent 对象

        参数:
            cfg: Configure 配置对象

        返回:
            Optional[DataContent]: 数据内容对象，解析失败返回None
        """
        if not self.dat_text and not self.dat_bytes:
            logging.error("CFF 文件中未找到 DAT 数据部分")
            return None

        temp_dir = self.file_path.parent
        temp_cfg_path = temp_dir / "_temp_cff.cfg"
        temp_dat_path = temp_dir / "_temp_cff.dat"

        try:
            temp_cfg_path.write_text(self.cfg_text, encoding="utf-8", errors="replace")

            if cfg.data_type.value == "ASCII":
                temp_dat_path.write_text(self.dat_text, encoding="utf-8", errors="replace")
            else:
                temp_dat_path.write_bytes(self.dat_bytes)

            cf = ComtradeFile.from_path(temp_cfg_path)
            return DataContent(cfg=cfg, file_name=cf)
        except Exception as e:
            logging.error(f"解析 DAT 数据失败: {e}")
            return None
        finally:
            if temp_cfg_path.exists():
                temp_cfg_path.unlink()
            if temp_dat_path.exists():
                temp_dat_path.unlink()

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> "CffFile":
        """从文件路径创建 CffFile 对象

        参数:
            file_path: CFF 文件路径

        返回:
            CffFile: CFF 文件对象
        """
        return cls(file_path)
