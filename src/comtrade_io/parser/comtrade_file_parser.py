#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from comtrade_io.model.comtrade import Comtrade
from comtrade_io.model.comtrade_file import ComtradeFile
from comtrade_io.model.configure import Configure
from comtrade_io.model.description import Description
from comtrade_io.model.equipment import EquipmentGroup
from comtrade_io.parser.cff import CffFile
from comtrade_io.parser.cfg.cfg_file_parser import CfgFileParser
from comtrade_io.parser.data import DataContent
from comtrade_io.parser.dfr import DfrFile
from comtrade_io.parser.dmf.dmf_element import DmfElement
from comtrade_io.parser.inf import Information
from comtrade_io.utils import get_logger

logger = get_logger()


class ComtradeFileParser(BaseModel):
    """COMTRADE 文件解析器

    支持从以下格式解析 COMTRADE 数据：
    - 传统多文件格式 (CFG + DAT + INF/HDR/DMF)
    - CFF 单文件格式 (CFG + DAT + INF 合并为一个文件)
    - DFR 格式 (WNDR 专有格式)

    解析流程：
    1. 根据文件扩展名判断文件类型（多文件 / CFF / DFR）
    2. 解析 CFG 配置（通道定义、采样率、时间信息等）
    3. 可选解析 DMF/INF 设备拓扑信息（母线、线路、变压器）
    4. 读取 DAT 数据文件，转换为 DataFrame
    5. 合并配置、设备信息、数据为 Comtrade 对象
    """

    @classmethod
    def _create_comtrade(
        cls,
        file: ComtradeFile,
        cfg: Configure,
        eg: EquipmentGroup | None = None,
        data: pd.DataFrame | None = None,
    ) -> Comtrade:
        """组装 Comtrade 对象

        将解析好的配置、设备拓扑和数据合并为完整的 Comtrade 对象。

        参数:
            file: 文件路径信息
            cfg: 配置对象（通道、采样率等）
            eg: 设备拓扑对象（母线、线路、变压器信息），从 DMF/INF 解析获得
            data: DAT 数据内容（DataFrame 格式）

        返回:
            组装完成的 Comtrade 对象
        """
        _model = cls.from_configure(cfg)
        if eg:
            _model.from_equipment_group(eg)
        else:
            _model.generate_equipment_group()
        _model.file = file
        _model.data = data
        return _model

    @classmethod
    def from_configure(cls, cfg: Configure) -> Comtrade:
        """从 Configure 配置对象创建 Comtrade 对象

        将配置对象作为 cfg 字段传入，并初始化 DMF/INF 所需的
        Description 描述信息（从 header 提取厂站名和录波器名）。

        参数:
            cfg: Configure 配置对象

        返回:
            Comtrade 实例（不含 data 和设备拓扑信息）
        """
        return Comtrade(
            cfg=cfg,
            description=Description(
                version=cfg.header.version,
                station_name=cfg.header.station,
                rec_dev_name=cfg.header.recorder,
            ),
        )

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> Comtrade | None:
        """从 COMTRADE 文件反序列化为 Comtrade 对象

        自动检测文件类型：
        - .cff → CFF 单文件格式
        - .dfr → DFR 格式
        - 其他 → 传统多文件格式（根据 CFG 文件查找同名 DAT/INF/DMF 文件）

        CFF/DFR 格式直接解析单文件；多文件格式需要先解析 CFG 配置，
        再按需解析 DMF/INF 设备拓扑信息，最后读取 DAT 数据。

        参数:
            file_name: COMTRADE 文件路径（CFG / CFF / DFR 均可）

        返回:
            Comtrade | None: 解析成功返回 Comtrade 对象，失败返回 None
        """
        cf = ComtradeFile.from_path(file_name)

        if cf.cff_path.is_enabled():
            return cls._from_cff(cf)

        if cf.dfr_path.is_enabled():
            return cls._from_dfr(cf)

        configure = CfgFileParser.from_file(file_name=cf)
        if configure is None:
            return None

        eg = DmfElement.from_file(file_name=cf)
        if eg is None:
            eg = Information.from_file(file_name=cf)

        dc = DataContent(cfg=configure, file_name=cf)
        return cls._create_comtrade(file=cf, cfg=configure, eg=eg, data=dc.data)

    @classmethod
    def _from_cff(cls, cf: ComtradeFile) -> Comtrade | None:
        """从 CFF 单文件格式加载 Comtrade 对象

        CFF 格式将 CFG、DAT（含 ASCII/BINARY）、INF 合并为一个 .cff 文件，
        通过 "--- file type XXX ---" 标记分隔各段。

        参数:
            cf: 文件路径信息，需包含有效的 .cff 文件路径

        返回:
            Comtrade | None: 解析成功返回 Comtrade 对象，失败返回 None
        """
        cff_file = CffFile.from_file(cf.cff_path.path)
        configure = cff_file.to_configure()
        if configure is None:
            return None
        eg = cff_file.to_information()
        data = cff_file.to_data_content(configure)
        return cls._create_comtrade(file=cf, cfg=configure, eg=eg, data=data)

    @classmethod
    def _from_dfr(cls, cf: ComtradeFile) -> Comtrade | None:
        """从 DFR 格式加载 Comtrade 对象

        DFR 格式是部分故障录波器使用的专有格式（WNDR），
        头部包含 WNDR 格式的通道定义文本，数据段为固定帧长的二进制格式。
        解析时先将 WNDR 头转换为标准 CFG 文本，再读取二进制数据。

        参数:
            cf: 文件路径信息，需包含有效的 .dfr 文件路径

        返回:
            Comtrade | None: 解析成功返回 Comtrade 对象，失败返回 None
        """
        dfr_file = DfrFile.from_file(cf.dfr_path.path)
        configure = dfr_file.to_configure()
        if configure is None:
            return None
        data = dfr_file.to_data_content(configure)
        return cls._create_comtrade(file=cf, cfg=configure, eg=None, data=data)
