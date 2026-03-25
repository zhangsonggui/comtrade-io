#!/usr/bin/env python
# -*- coding: utf-8 -*-
import io
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import Field

from comtrade_io.cfg import Configure
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.data import DataContent
from comtrade_io.dmf import AnalogChannel, ComtradeModel, StatusChannel
from comtrade_io.dmf.bus import Bus
from comtrade_io.dmf.line import Line
from comtrade_io.dmf.transformer import Transformer
from comtrade_io.inf.inf import InfInfo
from comtrade_io.utils import get_logger

logging = get_logger()


class Comtrade(ComtradeModel):
    file: ComtradeFile = Field(default_factory=ComtradeFile, description="文件路径")
    cfg: Configure = Field(..., description="参数配置文件")
    dat: Optional[DataContent] = Field(default=None, description="故障数据")

    def model_dump_json(self, *, indent: int | None = None, **kwargs) -> str:
        """
        将Comtrade模型转换为JSON字符串（不包含dat、cfg、file字段）
        """
        data = self.model_dump(mode='python')
        data.pop("cfg", None)
        data.pop("dat", None)
        data.pop("file", None)
        return self._to_json(data, indent)

    @staticmethod
    def _to_json(data: dict, indent: int | None = None) -> str:
        import json
        from uuid import UUID

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

    def get_data(self) -> pd.DataFrame:
        return self.dat.data

    def get_analog_channel(self, index: int) -> Optional[AnalogChannel]:
        analog = super().get_analog_channel_info(index)
        analog.data = self.dat.data.iloc[:, index + 1].to_numpy()
        return analog

    def get_status_channel(self, index: int) -> Optional[StatusChannel]:
        digital = super().get_status_channel_info(index)
        digital.data = self.dat.data.iloc[:, index + self.cfg.channel_num.analog + 1].to_numpy()
        return digital

    def _load_digital_data(self, channels: list, data: pd.DataFrame):
        for chn in channels:
            if chn and chn.index is not None:
                col_index = self.cfg.channel_num.analog + chn.index + 1
                chn.data = data.iloc[:, col_index].to_numpy() if col_index < data.shape[1] else None

    @staticmethod
    def _load_analog_channels(channels: tuple, data: pd.DataFrame):
        for chn in channels:
            if chn:
                col_index = chn.index + 1
                chn.data = data.iloc[:, col_index].to_numpy() if col_index < data.shape[1] else None

    def get_line(self, name: str) -> Line | None:
        line = super().get_line_info(name)
        if line is None or self.dat is None:
            return line
        data = self.dat.data
        if data is None:
            return line
        for current in line.currents:
            self._load_analog_channels((current.ia, current.ib, current.ic, current.i0), data)
        for bus in line.buses:
            self._load_analog_channels(
                (bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.ul, bus.voltage.un), data)
        self._load_digital_data(line.stas, data)
        return line

    def get_bus(self, name: str) -> Bus | None:
        bus = super().get_bus_info(name)
        if bus is None or self.dat is None:
            return bus
        data = self.dat.data
        if data is None:
            return bus
        self._load_analog_channels(
            (bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.ul, bus.voltage.un), data)
        self._load_digital_data(bus.anas, data)
        self._load_digital_data(bus.stas, data)
        return bus

    def get_transformer(self, name: str) -> Transformer | None:
        transformer = super().get_transformer_info(name)
        if transformer is None or self.dat is None:
            return transformer
        data = self.dat.data
        if data is None:
            return transformer
        for winding in transformer.transWinds:
            self._load_analog_channels(
                (winding.voltage.ua, winding.voltage.ub, winding.voltage.uc,
                 winding.voltage.ul, winding.voltage.un), data)
            for current in winding.currents:
                self._load_analog_channels((current.ia, current.ib, current.ic, current.i0), data)
        self._load_digital_data(transformer.anas, data)
        self._load_digital_data(transformer.stas, data)
        return transformer

    @classmethod
    def from_cff(cls, file_name: str | Path) -> "Comtrade | None":
        """
        从 CFF（单文件格式）加载 Comtrade 对象。

        CFF 是 COMTRADE 2013 版引入的合并格式：CFG、DAT 及可选的 INF、HDR
        内容全部存储在一个文件中，各节以哨兵行分隔。工作方式类似于将
        "装订成册"的文件拆回各自独立的部分，再交给现有解析器处理。

        参数:
            file_name: .cff 文件路径
        """
        from comtrade_io.cff_splitter import split_cff

        cf = ComtradeFile.from_path(file_name)
        if not cf.cff_path.is_enabled():
            return None

        sections = split_cff(cf.cff_path.path)

        # Configure.from_str() already exists — the CFG section is plain text.
        configure = Configure.from_str(sections.cfg)
        if configure is None:
            return None

        # DataContent.from_str() bypasses the filesystem for in-memory DAT data.
        data_content = DataContent.from_str(
            dat_str=sections.dat_text,
            dat_bytes=sections.dat_bytes,
            cfg=configure,
        )

        data_model = ComtradeModel.from_cfg(configure)

        # Optional INF — InfInfo.from_stream() reads from a StringIO.
        inf_info: Optional[InfInfo] = None
        if sections.inf is not None:
            try:
                inf_info = InfInfo.from_stream(io.StringIO(sections.inf))
            except Exception as e:
                logging.warning(f"CFF INF section could not be parsed, skipping: {e}")

        # HDR has no structured parser and no field on ComtradeModel — log and discard.
        if sections.hdr is not None:
            logging.debug("CFF HDR section present but not stored (no field on ComtradeModel)")

        # DMF is never embedded in a CFF — look for a sidecar file as usual.
        if cf.dmf_path.is_enabled():
            data_model = ComtradeModel.from_file(file_name=cf, cfg=configure) or data_model

        return cls(
            file=cf,
            cfg=configure,
            dat=data_content,
            station_name=data_model.station_name,
            version=data_model.version,
            rec_dev_name=data_model.rec_dev_name,
            buses=data_model.buses,
            lines=data_model.lines,
            transformers=data_model.transformers,
            analog_channels=data_model.analog_channels,
            status_channels=data_model.status_channels,
        )

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> "Comtrade | None":
        """
        从文件名反序列化Comtrade对象

        参数:
            file_name: 文件名称，可以是cfg、dat、inf及dmf任意文件名，后缀名不做要求。
                       传入 .cff 文件时自动走 CFF 单文件解析路径。
        """
        # CFF branch: single combined file (COMTRADE 2013+).
        if isinstance(file_name, (str, Path)) and Path(file_name).suffix.lower() == '.cff':
            return cls.from_cff(file_name)

        # Original multi-file branch (cfg + dat [+ dmf/hdr/inf]) — unchanged.
        cf = ComtradeFile.from_path(file_name)
        if not cf.cfg_path.is_enabled():
            return None
        configure = Configure.from_file(file_name=cf)
        if configure is None:
            return None

        data_model_fault = ComtradeModel.from_file(file_name=cf, cfg=configure)
        if data_model_fault is None:
            data_model_fault = ComtradeModel.from_cfg(configure)
        data_content = DataContent(cfg=configure, file_name=cf)
        result = cls(
            file=cf,
            cfg=configure,
            dat=data_content,
            station_name=data_model_fault.station_name,
            version=data_model_fault.version,
            rec_dev_name=data_model_fault.rec_dev_name,
            buses=data_model_fault.buses,
            lines=data_model_fault.lines,
            transformers=data_model_fault.transformers,
            analog_channels=data_model_fault.analog_channels,
            status_channels=data_model_fault.status_channels,
        )
        return result

    def save_comtrade(self, output_file_path: ComtradeFile | Path | str, data_type: str = "BINARY"):
        output_file_path = ComtradeFile.from_path(output_file_path)
        self.cfg.write_file(output_file_path)
        self.dat.write_file(output_file_path, data_type=data_type)
        return (f"文件保存成功："
                f"参数文件位置：{output_file_path.cfg_path.path}，"
                f"数据文件位置：{output_file_path.dat_path.path},"
                f"模型文件位置{output_file_path.dmf_path.path}")

    def save_json(self, output_file_path: Path | str, indent: int | None = None):
        data = self.model_dump(mode='python')
        data.pop("cfg", None)
        data.pop("file", None)
        if self.dat is not None and self.dat.data is not None:
            df = self.dat.data
            analog_list = data.get("analog_channels", [])
            for channel in analog_list:
                if channel.get("index") is not None:
                    col_index = channel["index"] + 2
                    if col_index < df.shape[1]:
                        channel["data"] = df.iloc[:, col_index].tolist()
            status_list = data.get("status_channels", [])
            for channel in status_list:
                if channel.get("index") is not None:
                    col_index = self.cfg.channel_num.analog + channel["index"] + 2
                    if col_index < df.shape[1]:
                        channel["data"] = df.iloc[:, col_index].tolist()
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(self._to_json(data, indent))
        logging.info(f"json数据写入{output_file_path}成功")
        return True
