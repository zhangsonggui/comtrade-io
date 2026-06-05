#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Optional, TYPE_CHECKING, Union

import pandas as pd
from pydantic import BaseModel, Field

from comtrade_io.model.configure import Configure
from comtrade_io.model.equipment import EquipmentGroup
from comtrade_io.parser.cfg import CfgFile
from comtrade_io.utils import FilePath, get_logger

if TYPE_CHECKING:
    from comtrade_io.model.comtrade import Comtrade

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
    def from_path(cls, file_path: Union[str, Path, "ComtradeFile"]) -> "ComtradeFile":
        """根据路径创建 ComtradeFile 对象"""
        if isinstance(file_path, ComtradeFile):
            return file_path

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
    def from_file(cls, file_name: str | Path) -> Comtrade:
        """从 COMTRADE 文件解析为 Comtrade 对象

        自动检测文件类型：.cff / .dfr / 传统多文件格式。

        参数:
            file_name: COMTRADE 文件路径（CFG / CFF / DFR 均可）

        返回:
            Comtrade | None: 解析成功返回 Comtrade 对象，失败返回 None
        """
        cf = cls.from_path(file_name)

        if cf.cff_path.is_enabled():
            return cls._from_cff(cf)

        if cf.dfr_path.is_enabled():
            return cls._from_dfr(cf)

        configure = CfgFile.from_file(file_name=cf)
        if configure is None:
            return None

        from comtrade_io.parser.dmf import DmfFile
        from comtrade_io.parser.inf import InfFile

        eg = DmfFile.from_file(file_name=cf)
        if eg is None:
            inf = InfFile.from_file(file_name=cf)
            eg = inf.to_equipment_group() if inf else None

        from comtrade_io.parser.dat import DatFile

        data = DatFile.from_file(configure, cf)
        return cls._create_comtrade(file=cf, cfg=configure, eg=eg, data=data)

    @classmethod
    def _from_cff(cls, cf: "ComtradeFile") -> Optional["Comtrade"]:
        from comtrade_io.parser.cff import CffFile

        cff_file = CffFile.from_file(cf.cff_path.path)
        configure = cff_file.to_configure()
        if configure is None:
            return None
        eg = cff_file.to_information()
        data = cff_file.to_data_content(configure)
        return cls._create_comtrade(file=cf, cfg=configure, eg=eg, data=data)

    @classmethod
    def _from_dfr(cls, cf: "ComtradeFile") -> Optional["Comtrade"]:
        from comtrade_io.parser.dfr import DfrFile

        dfr_file = DfrFile.from_file(cf.dfr_path.path)
        configure = dfr_file.to_configure()
        if configure is None:
            return None
        data = dfr_file.to_data_content(configure)
        return cls._create_comtrade(file=cf, cfg=configure, eg=None, data=data)

    @classmethod
    def _create_comtrade(
        cls,
        file: "ComtradeFile",
        cfg: Configure,
        eg: Optional[EquipmentGroup] = None,
        data: Optional[pd.DataFrame] = None,
    ) -> Optional["Comtrade"]:
        """组装 Comtrade 对象"""
        from comtrade_io.model.comtrade import Comtrade as ComtradeModel
        from comtrade_io.model.equipment import Bus, Line, Transformer

        analogs = dict(cfg.analogs)
        statuses = dict(cfg.statuses)
        if eg:
            for idx, ch in (eg.analogs or {}).items():
                analogs[idx] = ch
            for idx, ch in (eg.statuses or {}).items():
                statuses[idx] = ch

        buses = []
        lines = []
        transformers = []
        if eg:
            for bus_info in eg.buses or []:
                bus = Bus(
                    index=bus_info.index,
                    uuid=bus_info.uuid,
                    name=bus_info.name,
                    stas=bus_info.stas,
                    acvs=[
                        analogs.get(acv.index)
                        for acv in bus_info.acvs
                        if acv.index in analogs
                    ],
                    accs=bus_info.accs,
                    voltage=bus_info.voltage,
                    tv_install_site=bus_info.tv_install_site,
                    rated_primary_voltage=bus_info.rated_primary_voltage,
                    rated_secondary_voltage=bus_info.rated_secondary_voltage,
                )
                buses.append(bus)

            for line_info in eg.lines or []:
                line = Line(
                    index=line_info.index,
                    uuid=line_info.uuid,
                    name=line_info.name,
                    stas=line_info.stas,
                    acvs=[
                        analogs.get(acv.index)
                        for acv in line_info.acvs
                        if acv.index in analogs
                    ],
                    accs=[
                        analogs.get(acc.index)
                        for acc in line_info.accs
                        if acc.index in analogs
                    ],
                    impedance=line_info.impedance,
                    capacitance=line_info.capacitance,
                    mutual_inductance=line_info.mutual_inductance,
                    line_length=line_info.line_length,
                    currents=line_info.currents,
                    current_bran_num=line_info.current_bran_num,
                    bus_index=line_info.bus_index,
                    buses=line_info.buses,
                )
                lines.append(line)

            for tr_info in eg.transformers or []:
                transformer = Transformer(
                    index=tr_info.index,
                    uuid=tr_info.uuid,
                    name=tr_info.name,
                    stas=tr_info.stas,
                    acvs=[
                        analogs.get(acv.index)
                        for acv in tr_info.acvs
                        if acv.index in analogs
                    ],
                    accs=[
                        analogs.get(acc.index)
                        for acc in tr_info.accs
                        if acc.index in analogs
                    ],
                    capacity=tr_info.capacity,
                    winding_num=tr_info.winding_num,
                    trans_winds=tr_info.trans_winds,
                )
                transformers.append(transformer)

        comtrade = ComtradeModel(
            file=file,
            cfg=cfg,
            data=data,
            buses=buses,
            lines=lines,
            transformers=transformers,
        )
        logger.info("Comtrade对象生成完成")
        return comtrade

    def __str__(self) -> str:
        return (
            f"ComtradeFile(cfg_path={self.cfg_path.path}, dat_path={self.dat_path.path}, "
            f"cff_path={self.cff_path.path}, dmf_path={self.dmf_path.path}, "
            f"hdr_path={self.hdr_path.path}, inf_path={self.inf_path.path}, "
            f"dfr_path={self.dfr_path.path})"
        )
