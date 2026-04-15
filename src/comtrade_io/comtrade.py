#!/usr/bin/env python
# -*- coding: utf-8 -*-
from io import BytesIO, StringIO
from pathlib import Path
from typing import Optional

import pandas as pd
from comtrade_io.cff import CffFile
from comtrade_io.cfg import Configure
from comtrade_io.channel.analog import Analog
from comtrade_io.channel.status import Status
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.comtrade_model import ComtradeModel
from comtrade_io.data import DataContent
from comtrade_io.dmf.dmf_element import DmfElement
from comtrade_io.equipment.bus import Bus
from comtrade_io.equipment.line import Line
from comtrade_io.equipment.transformer import Transformer
from comtrade_io.exporters import export_format
from comtrade_io.inf import Information
from comtrade_io.utils import get_logger
from pydantic import Field

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
                return convert(obj)

        data = process(data)
        return json.dumps(data, ensure_ascii=False, default=str, indent=indent)

    def get_data(self) -> pd.DataFrame:
        return self.dat.data

    def get_analog_channel(self, index: int) -> Optional[Analog]:
        """
        根据通道标识获取模拟量通道，并加载通道数据
        """
        analog = self.get_analog_channel_info(index)
        analog.data = self.dat.data.iloc[:, index + 1].to_numpy()
        return analog

    def get_status_channel(self, index: int) -> Optional[Status]:
        """
        根据通道标识获取状态量通道，并加载通道数据
        """
        digital = self.get_status_channel_info(index)
        digital.data = self.dat.data.iloc[:, index + self.cfg.channel_num.analog + 1].to_numpy()
        return digital

    def _load_digital_data(self, channels: list, data: pd.DataFrame):
        """加载数字量通道数据到通道对象列表"""
        for chn in channels:
            if chn and chn.index is not None:
                col_index = self.cfg.channel_num.analog + chn.index + 1
                chn.data = data.iloc[:, col_index].to_numpy() if col_index < data.shape[1] else None

    @staticmethod
    def _load_analog_channels(channels: tuple, data: pd.DataFrame):
        """加载模拟量通道数据（ia, ib, ic, i0 或 ua, ub, uc, ul, un）"""
        for chn in channels:
            if chn:
                col_index = chn.index + 1
                chn.data = data.iloc[:, col_index].to_numpy() if col_index < data.shape[1] else None

    def get_line(self, name: str) -> Line | None:
        """
        根据名称获取线路，并加载通道数据

        参数:
            name: 线路名称

        返回:
            线路对象，如果未找到则返回None
        """
        line = self.get_line_info(name)
        if line is None or self.dat is None:
            return line

        data = self.dat.data
        if data is None:
            return line

        # 加载电流通道数据
        for current in line.currents:
            self._load_analog_channels((current.ia, current.ib, current.ic, current.i0), data)

        # 加载电压通道数据
        for bus in line.buses:
            self._load_analog_channels((bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.ul, bus.voltage.un),
                                       data)

        # 加载开关量通道数据
        self._load_digital_data(line.stas, data)

        return line

    def get_bus(self, name: str) -> Bus | None:
        """
        根据名称获取母线，并加载通道数据

        参数:
            name: 母线名称

        返回:
            母线对象，如果未找到则返回None
        """
        bus = super().get_bus_info(name)
        if bus is None or self.dat is None:
            return bus

        data = self.dat.data
        if data is None:
            return bus

        # 加载电压通道数据
        self._load_analog_channels((bus.voltage.ua, bus.voltage.ub, bus.voltage.uc, bus.voltage.ul, bus.voltage.un),
                                   data)

        # 加载模拟通道和开关量通道数据
        self._load_digital_data(bus.anas, data)
        self._load_digital_data(bus.stas, data)

        return bus

    def get_transformer(self, name: str) -> Transformer | None:
        """
        根据名称获取变压器，并加载通道数据

        参数:
            name: 变压器名称

        返回:
            变压器对象，如果未找到则返回None
        """
        transformer = super().get_transformer_info(name)
        if transformer is None or self.dat is None:
            return transformer

        data = self.dat.data
        if data is None:
            return transformer

        # 加载各绕组的电压和电流通道数据
        for winding in transformer.trans_winds:
            self._load_analog_channels(
                    (winding.voltage.ua, winding.voltage.ub, winding.voltage.uc, winding.voltage.ul,
                     winding.voltage.un),
                    data)
            for current in winding.currents:
                self._load_analog_channels((current.ia, current.ib, current.ic, current.i0), data)

        # 加载模拟通道和开关量通道数据
        self._load_digital_data(transformer.anas, data)
        self._load_digital_data(transformer.stas, data)

        return transformer

    @staticmethod
    def _sync_channels(configure: Configure, comtrade_model: ComtradeModel) -> None:
        """同步Configure和ComtradeModel中的通道信息"""
        for idx, cfg_analog in configure.analogs.items():
            if idx in comtrade_model.analogs:
                cm_analog = comtrade_model.analogs.get(idx)
                cm_analog.sync_from(cfg_analog)

        for idx, cfg_status in configure.statuses.items():
            if idx in comtrade_model.statuses:
                cm_status = comtrade_model.statuses.get(idx)
                cm_status.sync_from(cfg_status)

    @classmethod
    def _create_comtrade(cls,
                         file: ComtradeFile,
                         cfg: Configure,
                         dat: DataContent,
                         cm: ComtradeModel = None) -> "Comtrade":
        """创建Comtrade对象的共享方法"""
        if cm:
            cls._sync_model_with_configure(cfg, cm)
        else:
            cm = cls._generate_model(cfg)

        return cls(
                file=file,
                cfg=cfg,
                dat=dat,
                description=cm.description,
                buses=cm.buses,
                lines=cm.lines,
                transformers=cm.transformers,
                analogs=cm.analogs,
                statuses=cm.statuses,
        )

    @classmethod
    def _sync_model_with_configure(cls, configure: Configure, _model: ComtradeModel) -> None:
        """同步Configure和ComtradeModel的共享方法"""
        cls._sync_channels(configure, _model)
        _model.description.version = configure.header.version
        configure.analogs = _model.analogs
        configure.statuses = _model.statuses

    @classmethod
    def _generate_model(cls, cfg: Configure) -> ComtradeModel:
        """生成ComtradeModel对象"""
        model = ComtradeModel()
        model.analogs = cfg.analogs
        model.statuses = cfg.statuses
        return model

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> "Comtrade|None":
        """从文件名反序列化Comtrade对象"""
        cf = ComtradeFile.from_path(file_name)

        if cf.cff_path.is_enabled():
            return cls._from_cff(cf)

        configure = Configure.from_file(file_name=cf)
        if configure is None:
            return None

        _model = DmfElement.from_file(file_name=cf)
        if _model is None:
            _model = Information.from_file(file_name=cf)

        data_content = DataContent(cfg=configure, file_name=cf)
        return cls._create_comtrade(cf, configure, data_content, _model)

    @classmethod
    def _from_cff(cls, cf: ComtradeFile) -> "Comtrade|None":
        """从 CFF 单文件加载 Comtrade 对象"""
        cff_file = CffFile.from_file(cf.cff_path.path)
        configure = cff_file.to_configure()
        if configure is None:
            return None
        _model = cff_file.to_information()
        data_content = cff_file.to_data_content(configure)
        return cls._create_comtrade(cf, configure, data_content, _model)

    @export_format
    def save_comtrade(self, output_file_path: ComtradeFile | Path | str, **kwargs):
        """
        将 comtrade 对象保存为文件

        参数:
            output_file_path: 保存路径
            format: 导出格式 (multi_file/cff/json/csv), 默认multi_file
            data_format: dat文件格式 (ASCII/BINARY/BINARY32/FLOAT32), 默认BINARY
            **kwargs: 其他参数
        """
        pass

    def _export_multi_file(self, output_path: str | Path | ComtradeFile,
                           data_format: str, **kwargs) -> str:
        """导出多文件格式"""
        cf = ComtradeFile.from_path(output_path)
        self.cfg.write_file(cf)
        self.dat.write_file(cf, data_type=data_format)
        if cf.inf_path.path:
            self.write_inf(str(cf.inf_path.path))
        if cf.dmf_path.path:
            self.write_dmf(str(cf.dmf_path.path))
        return f"文件保存成功: cfg={cf.cfg_path.path}, dat={cf.dat_path.path}"

    def _export_cff(self, output_path: str | Path | ComtradeFile,
                    data_format: str, **kwargs) -> str:
        """导出CFF单文件格式"""
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
        sections.append(str(self.cfg))

        sections.append("--- file type DAT ---")
        if data_format == "ASCII":
            buffer = StringIO()
            self.dat.data.to_csv(buffer, header=False, index=False)
            sections.append(buffer.getvalue())
        else:
            buffer = BytesIO()
            from tempfile import NamedTemporaryFile
            import os
            with NamedTemporaryFile(delete=False, suffix='.dat') as tmp:
                tmp_path = tmp.name
            try:
                tmp_cf = ComtradeFile.from_path(tmp_path)
                self.dat.write_file(tmp_cf, data_type=data_format)
                dat_bytes = Path(tmp_path).read_bytes()
                sections.append(dat_bytes.decode('latin-1'))
            finally:
                os.unlink(tmp_path)

        inf_content = self.to_inf()
        if inf_content:
            sections.append("--- file type INF ---")
            sections.append(inf_content)

        with open(cff_path, 'w', encoding='gbk') as f:
            f.write('\n'.join(sections))

        logging.info(f"CFF文件{cff_path}写入成功")
        return f"文件保存成功: {cff_path}"

    def _export_json(self, output_path: str | Path | ComtradeFile,
                     data_format: str, **kwargs) -> bool:
        """导出JSON格式"""
        path = Path(output_path) if not isinstance(output_path, ComtradeFile) else \
            (output_path.cfg_path.path.parent / (
                        output_path.cfg_path.path.stem + '.json') if output_path.cfg_path.path else None)
        if not path:
            raise ValueError("无法确定JSON输出路径")
        if path.suffix.lower() != '.json':
            path = path.with_suffix('.json')
        return self.save_json(path, indent=kwargs.get('indent'))

    def _export_csv(self, output_path: str | Path | ComtradeFile,
                    data_format: str, **kwargs) -> bool:
        """导出CSV格式"""
        path = Path(output_path) if not isinstance(output_path, ComtradeFile) else \
            (output_path.cfg_path.path.parent / (
                        output_path.cfg_path.path.stem + '.csv') if output_path.cfg_path.path else None)
        if not path:
            raise ValueError("无法确定CSV输出路径")
        if path.suffix.lower() != '.csv':
            path = path.with_suffix('.csv')

        headers = ['Point', 'Time']
        for idx in sorted(self.cfg.analogs.keys()):
            a = self.cfg.analogs[idx]
            headers.append(f"{a.name or f'A{idx}'}")
        for idx in sorted(self.cfg.statuses.keys()):
            s = self.cfg.statuses[idx]
            headers.append(f"{s.name or f'D{idx}'}")

        self.dat.data.to_csv(path, header=headers if kwargs.get('include_headers', True) else False, index=False)
        logging.info(f"CSV文件{path}写入成功")
        return True

    def save_json(self, output_file_path: Path | str,
                  indent: int | None = None):
        """将Comtrade对象保存为JSON文件（包含dat数据）"""
        data = self.model_dump(mode='python')
        data.pop("cfg", None)
        data.pop("file", None)

        if self.dat is not None and self.dat.data is not None:
            df = self.dat.data
            analog_list = data.get("analogs", [])
            for ch in analog_list:
                if isinstance(ch, dict) and ch.get("index") is not None:
                    col_idx = ch["index"] + 2
                    if col_idx < df.shape[1]:
                        ch["data"] = df.iloc[:, col_idx].tolist()
            status_list = data.get("statuses", [])
            for ch in status_list:
                if isinstance(ch, dict) and ch.get("index") is not None:
                    col_idx = self.cfg.channel_num.analog + ch["index"] + 2
                    if col_idx < df.shape[1]:
                        ch["data"] = df.iloc[:, col_idx].tolist()

        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(self._to_json(data, indent))
        logging.info(f"json数据写入{output_file_path}成功")
        return True
