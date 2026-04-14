#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

from comtrade_io.utils import get_logger

logging = get_logger()


class FilePath(BaseModel):
    """文件路径类

    封装文件路径及其状态信息，包括文件是否存在、是否为空、是否可读等。

    属性:
        path: 文件路径
        is_exists: 文件是否存在
        is_empty: 文件是否为空
        is_readable: 文件是否可读
    """
    path: Optional[Path] = Field(default=None, description="文件路径")
    is_exists: bool = Field(default=True, description="文件是否存在")
    is_empty: bool = Field(default=False, description="文件是否为空")
    is_readable: bool = Field(default=True, description="文件是否可读")

    def model_post_init(self, context: Any, /) -> None:
        """初始化后检查文件状态

        参数:
            context: Pydantic上下文对象
        """
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
        """检查文件是否可用

        文件可用的条件：文件存在、非空、可读。

        返回:
            bool: 文件是否可用
        """
        if self.path is None:
            return False
        return all([
            not self.is_empty,
            self.is_exists,
            self.is_readable
        ])

    def __str__(self):
        """返回文件路径的字符串表示

        返回:
            str: 文件路径和可用性状态的字符串
        """
        return f"文件：{self.path}{'可用' if self.is_enabled() else '不可用'}"


class ComtradeFile(BaseModel):
    """COMTRADE 文件封装类

    包含 COMTRADE 相关的所有文件信息，包括 cfg, dat, cff, dmf, hdr, inf 等文件。

    属性:
        cfg_path: cfg配置文件信息
        dat_path: dat数据文件信息
        cff_path: cff单文件信息
        dmf_path: dmf模型文件信息
        hdr_path: hdr头文件信息
        inf_path: inf信息文件信息
    """
    cfg_path: FilePath = Field(default_factory=FilePath, description="cfg文件信息")
    dat_path: FilePath = Field(default_factory=FilePath, description="dat文件信息")
    cff_path: FilePath = Field(default_factory=FilePath, description="cff单文件信息")
    dmf_path: FilePath = Field(default_factory=FilePath, description="dmf文件信息")
    hdr_path: FilePath = Field(default_factory=FilePath, description="hdr文件信息")
    inf_path: FilePath = Field(default_factory=FilePath, description="inf文件信息")

    @classmethod
    def from_path(cls, file_path: Union[str, Path, 'ComtradeFile']) -> 'ComtradeFile':
        """根据路径创建 ComtradeFile 对象

        同时查找并验证 cfg, dat, cff, dmf, hdr, inf 文件。
        如果提供的是任意一个COMTRADE相关文件，会自动查找同目录下的其他相关文件。

        参数:
            file_path: 文件路径，可以是字符串、Path对象或ComtradeFile对象

        返回:
            ComtradeFile: 包含所有相关文件信息的ComtradeFile对象
        """
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
        """返回ComtradeFile对象的字符串表示

        返回:
            str: 包含所有文件路径的字符串
        """
        return (f"ComtradeFile(cfg_path={self.cfg_path.path}, dat_path={self.dat_path.path}, "
                f"cff_path={self.cff_path.path}, dmf_path={self.dmf_path.path}, "
                f"hdr_path={self.hdr_path.path}, inf_path={self.inf_path.path})")
