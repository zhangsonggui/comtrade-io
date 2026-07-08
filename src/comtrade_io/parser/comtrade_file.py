from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import BaseModel, Field

from . import CfgFile
from ..model.configure import Configure
from ..model.equipment import EquipmentGroup
from ..utils import FilePath, get_logger
from ..utils.timer import timer

if TYPE_CHECKING:
    from ..model.comtrade import Comtrade

logger = get_logger()


class ComtradeFile(BaseModel):
    """COMTRADE 文件封装类

    包含 COMTRADE 相关的所有文件信息，并提供从各种格式解析为 Comtrade 对象的方法。
    """

    cfg_path: FilePath = Field(default_factory=FilePath, description="cfg文件信息")
    dat_path: FilePath = Field(default_factory=FilePath, description="dat文件信息")
    cff_path: FilePath = Field(default_factory=FilePath, description="cff单文件信息")
    dmf_path: FilePath = Field(default_factory=FilePath, description="dmf文件信息")
    hdr_path: FilePath = Field(default_factory=FilePath, description="hdr文件信息")
    inf_path: FilePath = Field(default_factory=FilePath, description="inf文件信息")
    dfr_path: FilePath = Field(default_factory=FilePath, description="dfr单文件信息")

    @classmethod
    def from_path(cls, file_path: str | Path) -> "ComtradeFile":
        """根据路径创建 ComtradeFile 对象"""

        ALLOWED_SUFFIXES = {
            ".cfg": "cfg_path",
            ".dat": "dat_path",
            ".cff": "cff_path",
            ".dmf": "dmf_path",
            ".hdr": "hdr_path",
            ".inf": "inf_path",
            ".dfr": "dfr_path",
        }

        if file_path is None:
            return cls()
        if isinstance(file_path, str):
            file_str = file_path.strip()
            if file_str == "":
                return cls()
            file_path = Path(file_path)

        input_suffix = file_path.suffix
        input_suffix_lower = input_suffix.lower()
        target_attr = ALLOWED_SUFFIXES.get(input_suffix_lower)

        if input_suffix_lower == ".cff":
            result = cls()
            result.cff_path = FilePath(path=file_path)
            return result

        if input_suffix_lower == ".dfr":
            result = cls()
            result.dfr_path = FilePath(path=file_path)
            return result

        is_upper = input_suffix[1:].isupper() if input_suffix else False

        result = cls()
        for allowed_suffix, attr_name in ALLOWED_SUFFIXES.items():
            if allowed_suffix in (".cff", ".dfr"):
                continue
            if target_attr == attr_name:
                related_path = file_path
            else:
                new_suffix = (
                    allowed_suffix.upper() if is_upper else allowed_suffix.lower()
                )
                related_path = file_path.parent / (file_path.stem + new_suffix)

            file_path_obj = FilePath(path=related_path)
            setattr(result, attr_name, file_path_obj)
        return result

    @classmethod
    @timer(name="ComtradeFile.from_file")
    def from_file(cls, file_name: str | Path) -> Comtrade | None:
        """从传统 COMTRADE 多文件解析为 Comtrade 对象

        仅处理以 CFG/DAT 为核心的多文件格式；CFF 和 DFR 单文件请分别使用
        from_cff() 与 from_dfr()。

        参数:
            file_name: 传统 COMTRADE 文件路径（通常为 CFG / DAT / INF / DMF）

        返回:
            Comtrade | None: 解析成功返回 Comtrade 对象，失败返回 None
        """
        cf = cls.from_path(file_name)

        if cf.cff_path.path is not None or cf.dfr_path.path is not None:
            logger.info("from_file 跳过单文件格式，请使用 from_cff 或 from_dfr 读取")
            return None

        logger.info(f"开始读取传统 COMTRADE 多文件: {file_name}")
        configure = CfgFile.from_file(cf.cfg_path.path)
        if configure is None:
            logger.warning(f"未能读取 CFG 配置文件: {cf.cfg_path.path}")
            return None

        from . import DmfFile, InfFile

        eg = DmfFile.from_file(cf.dmf_path.path)
        if eg is None:
            inf = InfFile.from_file(cf.inf_path.path)
            eg = inf.to_equipment_group() if inf else None

        from .dat import DatFile

        data = DatFile.from_file(configure, cf.dat_path.path)
        logger.info(f"传统 COMTRADE 多文件读取完成: {file_name}")
        return cls._create_comtrade(cfg=configure, eg=eg, data=data)

    @classmethod
    def from_cff(cls, file_name: str | Path) -> Comtrade | None:
        """从 CFF 单文件解析为 Comtrade 对象"""
        from .cff import CffFile

        logger.info(f"开始读取 CFF 单文件: {file_name}")
        try:
            cff_file = CffFile.from_file(file_name)
            configure = cff_file.to_configure()
            if configure is None:
                logger.warning(f"未能从 CFF 解析配置: {file_name}")
                return None
            eg = cff_file.to_information()
            data = cff_file.to_data_content(configure)
            if data is None:
                logger.warning(f"未能从 CFF 解析数据: {file_name}")
                return None
        except Exception as e:
            logger.error(f"读取 CFF 单文件失败: {file_name}, {e}")
            return None
        logger.info(f"CFF 单文件读取完成: {file_name}")
        return cls._create_comtrade(cfg=configure, eg=eg, data=data)

    @classmethod
    def from_dfr(cls, file_name: str | Path) -> Comtrade | None:
        """从 DFR 单文件解析为 Comtrade 对象"""
        from .dfr import DfrFile

        logger.info(f"开始读取 DFR 单文件: {file_name}")
        try:
            dfr_file = DfrFile.from_file(file_name)
            configure = dfr_file.to_configure()
            if configure is None:
                logger.warning(f"未能从 DFR 解析配置: {file_name}")
                return None
            data = dfr_file.to_data_content(configure)
            if data is None:
                logger.warning(f"未能从 DFR 解析数据: {file_name}")
                return None
        except Exception as e:
            logger.error(f"读取 DFR 单文件失败: {file_name}, {e}")
            return None
        logger.info(f"DFR 单文件读取完成: {file_name}")
        return cls._create_comtrade(cfg=configure, eg=None, data=data)

    @classmethod
    def _create_comtrade(
        cls,
        cfg: Configure,
        eg: EquipmentGroup = None,
        data: pd.DataFrame = None,
    ) -> Comtrade | None:
        """组装 Comtrade 对象，DMF/INF信息缺失时由CfgToEquipment自动生成设备模型"""

        if eg is None:
            from ..utils.cfg_to_equipment import CfgToEquipment

            eg = CfgToEquipment.convert(cfg)
            logger.info(
                "设备信息文件不存在或为空，已通过CfgToEquipment从CFG自动生成设备模型"
            )
        else:
            eg.validate_and_supplement(cfg.analogs, cfg.statuses)
            logger.info("已基于CFG对设备模型进行校验补全")

        from ..model.comtrade import Comtrade

        comtrade = Comtrade(
            config=cfg,
            data=data,
            buses=eg.buses if eg else None,
            lines=eg.lines if eg else None,
            transformers=eg.transformers if eg else None,
        )
        if eg is not None:
            comtrade.from_equipment_group(eg)
        return comtrade

    def __str__(self) -> str:
        return (
            f"ComtradeFile(cfg_path={self.cfg_path.path}, dat_path={self.dat_path.path}, "
            f"cff_path={self.cff_path.path}, dmf_path={self.dmf_path.path}, "
            f"hdr_path={self.hdr_path.path}, inf_path={self.inf_path.path}, "
            f"dfr_path={self.dfr_path.path})"
        )
