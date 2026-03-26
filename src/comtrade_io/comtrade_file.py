#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from comtrade_io.utils import get_logger

logging = get_logger()


class FilePath(BaseModel):
    path: Optional[Path] = Field(default=None, description="文件路径")
    is_exists: bool = Field(default=True, description="文件是否存在")
    is_empty: bool = Field(default=False, description="文件是否为空")
    is_readable: bool = Field(default=True, description="文件是否可读")

    def model_post_init(self, context: Any, /) -> None:
        if self.path is None:
            return
        if self.path.exists():
            self.is_exists = True
            self.is_empty = self.path.stat().st_size == 0
            try:
                with open(self.path, "rb") as f:
                    f.read(1)
            except Exception:
                self.is_readable = False
        else:
            self.is_exists = False
            self.is_readable = False
            self.is_empty = True

    def is_enabled(self) -> bool:
        if self.path is None:
            return False
        return all([
            not self.is_empty,
            self.is_exists,
            self.is_readable
        ])

    def __str__(self):
        return f"文件：{self.path}{'可用' if self.is_enabled() else '不可用'}"


class ComtradeFile(BaseModel):
    """COMTRADE 文件封装，包含 cfg, dat, cff, dmf, hdr, inf 等文件信息"""
    cfg_path: FilePath = Field(default_factory=FilePath, description="cfg文件信息")
    dat_path: FilePath = Field(default_factory=FilePath, description="dat文件信息")
    cff_path: FilePath = Field(default_factory=FilePath, description="cff单文件信息")
    dmf_path: FilePath = Field(default_factory=FilePath, description="dmf文件信息")
    hdr_path: FilePath = Field(default_factory=FilePath, description="hdr文件信息")
    inf_path: FilePath = Field(default_factory=FilePath, description="inf文件信息")

    @classmethod
    def from_path(cls, file_path: Union[str, Path, 'ComtradeFile']) -> 'ComtradeFile':
        """根据路径创建 ComtradeFile 对象，同时查找并验证 cfg, dat, cff, dmf, hdr, inf 文件"""
        if isinstance(file_path, ComtradeFile):
            return file_path

        ALLOWED_SUFFIXES = {'.cfg': "cfg_path",
                            '.dat': "dat_path",
                            '.cff': "cff_path",
                            '.dmf': "dmf_path",
                            '.hdr': "hdr_path",
                            '.inf': "inf_path"}

        if file_path is None:
            return cls()
        if isinstance(file_path, str):
            file_str = file_path.strip()
            if file_str == '':
                return cls()
            file_path = Path(file_path)

        input_suffix = file_path.suffix
        input_suffix_lower = input_suffix.lower()
        target_attr = ALLOWED_SUFFIXES.get(input_suffix_lower)

        if input_suffix_lower == '.cff':
            result = cls()
            result.cff_path = FilePath(path=file_path)
            return result

        is_upper = input_suffix[1:].isupper() if input_suffix else False

        result = cls()
        for allowed_suffix, attr_name in ALLOWED_SUFFIXES.items():
            if allowed_suffix == '.cff':
                continue
            if target_attr == attr_name:
                related_path = file_path
            else:
                new_suffix = allowed_suffix.upper() if is_upper else allowed_suffix.lower()
                related_path = file_path.parent / (file_path.stem + new_suffix)

            file_path_obj = FilePath(path=related_path)
            setattr(result, attr_name, file_path_obj)
        return result

    def __str__(self) -> str:
        return (f"ComtradeFile(cfg_path={self.cfg_path.path}, dat_path={self.dat_path.path}, "
                f"cff_path={self.cff_path.path}, dmf_path={self.dmf_path.path}, "
                f"hdr_path={self.hdr_path.path}, inf_path={self.inf_path.path})")
