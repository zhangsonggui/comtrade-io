#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import Field

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
from comtrade_io.inf import Information
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
        """同步Configure和ComtradeModel中的通道信息

        按照index对比通道对象，使用Channel类的sync_from方法将Configure中的
        属性同步到ComtradeModel中的通道对象上。sync_from方法会处理更新逻辑：
        - ComtradeModel中为None的属性直接更新
        - Configure中为None的属性不更新

        参数:
            configure: Configure对象
            comtrade_model: ComtradeModel对象
        """
        # 同步模拟量通道：从cfg_analog同步到cm_analog
        for idx, cfg_analog in configure.analogs.items():
            if idx in comtrade_model.analogs:
                cm_analog = comtrade_model.analogs.get(idx)
                cm_analog.sync_from(cfg_analog)

        # 同步数字量通道：从cfg_status同步到cm_status
        for idx, cfg_status in configure.statuses.items():
            if idx in comtrade_model.statuses:
                cm_status = comtrade_model.statuses.get(idx)
                cm_status.sync_from(cfg_status)

    @classmethod
    def _create_comtrade(cls, cf: ComtradeFile, configure: Configure,
                         _model: ComtradeModel, data_content: DataContent) -> "Comtrade":
        """
        创建Comtrade对象的共享方法

        参数:
            cf: ComtradeFile 对象
            configure: Configure 配置对象
            _model: ComtradeModel 模型对象
            data_content: DataContent 数据内容对象

        返回:
            Comtrade: 创建的Comtrade对象
        """
        return cls(
                file=cf,
                cfg=configure,
                dat=data_content,
                description=_model.description,
                buses=_model.buses,
                lines=_model.lines,
                transformers=_model.transformers,
                analogs=_model.analogs,
                statuses=_model.statuses,
        )

    @classmethod
    def _sync_model_with_configure(cls, configure: Configure, _model: ComtradeModel) -> None:
        """
        同步Configure和ComtradeModel的共享方法

        参数:
            configure: Configure 配置对象
            _model: ComtradeModel 模型对象
        """
        cls._sync_channels(configure, _model)
        _model.description.version = configure.header.version
        configure.analogs = _model.analogs
        configure.statuses = _model.statuses

    @classmethod
    def from_file(cls, file_name: str | Path | ComtradeFile) -> "Comtrade|None":
        """
        从文件名反序列化Comtrade对象
        解析顺序：
        1.判断是否是单文件cff，如果是单文件直接解析单文件逻辑
        2.解析cfg文件，获取Configure对象，如果该文件不存在直接返回空
        3.解析dmf文件，获取ComtradeModel对象，如果dmf文件为空，进入第4步
        4.解析inf文件，获取ComtradeModel对象，如果inf文件不为空进入第5步，如果不为空进入第6步
        5.将Configure对象中的通道信息更新到ComtradeModel对象
        6.根据Configure对象中的模拟量、开关量通道名称、相别、单位按照规则生成分组及Bus、Line、Transformer对象
        7.解析dat文件，获取DataContent对象
        8.合并后形成Comtrade对象

        参数:
            file_name(str): 文件名称,可以是cfg、dat、cff、inf及dmf任意文件名，后缀名不做要求
        """
        cf = ComtradeFile.from_path(file_name)

        # 1.判断cff文件是否存在，进行cff文件分析
        if cf.cff_path.is_enabled():
            return cls._from_cff(cf)

        # 2.解析cfg文件
        configure = Configure.from_file(file_name=cf)
        if configure is None:
            return None

        # 3.解析dmf文件，获取ComtradeModel对象
        _model = DmfElement.from_file(file_name=cf)
        if _model is None:
            # 4. 解析inf文件，获取ComtradeModel对象
            _model = Information.from_file(file_name=cf)

        if _model:
            # 5.将Configure对象中的通信信息更新到ComtradeModel对象
            cls._sync_model_with_configure(configure, _model)
        else:
            # todo 6.根据Configure对象中的模拟量、开关量通道名称、相别、单位按照规则生成分组及Bus、Line、Transformer对象
            pass

        # 7.解析dat文件
        data_content = DataContent(cfg=configure, file_name=cf)

        # 8.创建并返回Comtrade对象
        return cls._create_comtrade(cf, configure, _model, data_content)

    @classmethod
    def _from_cff(cls, cf: ComtradeFile) -> "Comtrade|None":
        """
        从 CFF 单文件加载 Comtrade 对象（不生成临时文件）

        参数:
            cf: ComtradeFile 对象
        """
        cff_file = CffFile.from_file(cf.cff_path.path)

        # 直接从内存解析CFG，不生成临时文件
        configure = cff_file.to_configure()
        if configure is None:
            return None

        # 尝试从CFF解析INF
        _model = cff_file.to_information()
        if _model:
            # 同步通道信息
            cls._sync_model_with_configure(configure, _model)
        else:
            # 没有INF，创建空的ComtradeModel
            # todo 6.根据Configure对象中的模拟量、开关量通道名称、相别、单位按照规则生成分组及Bus、Line、Transformer对象
            _model = ComtradeModel()
            _model.analogs = configure.analogs
            _model.statuses = configure.statuses

        # 直接从内存解析DAT，不生成临时文件
        data_content = cff_file.to_data_content(configure)

        # 创建并返回Comtrade对象
        return cls._create_comtrade(cf, configure, _model, data_content)

    def save_comtrade(self, output_file_path: ComtradeFile | Path | str, data_type: str = "BINARY"):
        """
        将 comtrade 对象保存为文件
        参数:
            output_file_path(str) 保存路径，后缀名可选
            data_file_type(str) 保存格式，默认保存为二进制文件
        """
        output_file_path = ComtradeFile.from_path(output_file_path)

        self.cfg.write_file(output_file_path)
        self.dat.write_file(output_file_path, data_type=data_type)

        return (f"文件保存成功："
                f"参数文件位置：{output_file_path.cfg_path.path}，"
                f"数据文件位置：{output_file_path.dat_path.path},"
                f"模型文件位置{output_file_path.dmf_path.path}")

    def save_json(self, output_file_path: Path | str,
                  indent: int | None = None):
        """
        将Comtrade对象转换为JSON字符串（包含dat数据）
        """
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
