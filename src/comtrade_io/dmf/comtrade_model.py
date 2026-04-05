#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
COMTRADE数据模型模块

定义COMTRADE数据模型的主类ComtradeModel，用于表示完整的电力系统数据模型。
该模型包含母线、线路、变压器等设备，以及模拟量和开关量通道。
支持从XML文件读取、解析和写入数据模型。
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional
from xml.etree.ElementTree import Element

from pydantic import Field, model_serializer

from comtrade_io.cfg import Configure
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.dmf.analog_channel import AnalogChannel
from comtrade_io.dmf.bus import Bus
from comtrade_io.dmf.dmf_base_model import ComtradeBaseModel
from comtrade_io.dmf.line import Line
from comtrade_io.dmf.status_channel import StatusChannel
from comtrade_io.dmf.transformer import Transformer
from comtrade_io.inf import Information
from comtrade_io.utils import get_logger

logging = get_logger(__name__)


class ComtradeModel(ComtradeBaseModel):
    """
    COMTRADE数据模型类
    
    表示完整的电力系统数据模型，包含以下主要组成部分：
    - 母线（Bus）：电力系统中的节点
    - 线路（Line）：连接母线的输电线路
    - 变压器（Transformer）：改变电压等级的设备
    - 模拟通道（AnalogChannel）：采集模拟量的通道
    - 状态通道（StatusChannel）：采集开关量的通道
    
    该类提供从XML文件读取、XML元素解析、配置对象转换等方法，
    以及将数据模型写入XML文件的功能。
    
    属性:
        buses: 母线列表
        lines: 线路列表
        transformers: 变压器列表
        analog_channels: 模拟通道字典，键为通道索引
        status_channels: 状态通道字典，键为通道索引
    """
    buses: list[Bus] = Field(default_factory=list, description="母线")
    lines: list[Line] = Field(default_factory=list, description="线路")
    transformers: list[Transformer] = Field(default_factory=list, description="变压器")
    analog_channels: dict[int, AnalogChannel] = Field(default_factory=dict, description="模拟量通道")
    status_channels: dict[int, StatusChannel] = Field(default_factory=dict, description="开关量通道")

    @model_serializer(mode='wrap')
    def serialize_model(self, handler):
        data = handler(self)
        data['analog_channels'] = list(self.analog_channels.values())
        data['status_channels'] = list(self.status_channels.values())
        return data

    def get_bus_info(self, name: str) -> Bus | None:
        """
        根据名称获取母线信息
        
        参数:
            name: 母线名称
            
        返回:
            母线对象，如果未找到则返回None
        """
        return next((bus for bus in self.buses if bus.name == name), None)

    def get_line_info(self, name: str) -> Line | None:
        """
        根据名称获取线路信息
        
        参数:
            name: 线路名称
            
        返回:
            线路对象，如果未找到则返回None
        """
        return next((line for line in self.lines if line.name == name), None)

    def get_transformer_info(self, name: str) -> Transformer | None:
        """
        根据名称获取变压器信息
        
        参数:
            name: 变压器名称
            
        返回:
            变压器对象，如果未找到则返回None
        """
        return next((trans for trans in self.transformers if trans.name == name), None)

    def get_analog_channel_info(self, index: int) -> Optional[AnalogChannel]:
        """
        根据 index 获取模拟量通道

        参数:
            index(int): 通道索引
            
        返回:
            模拟量通道，未找到返回 None
        """
        return self.analog_channels.get(index)

    def get_ac_branch_by_ids(self, channel_ids: list[int]):
        """
        根据 index列表获取电压分组或电流分组

        参数:
            channel_ids(List[int])： 通道索引列表

        返回:
            模拟量通道分组，未找到返回 None
        """
        from comtrade_io.dmf.branch import ACVBranch, ACCBranch
        from comtrade_io.type import AnalogChannelFlag

        channel_ids = set(channel_ids)
        voltages = []
        currents = []
        for channel_id in channel_ids:
            channel = self.analog_channels.get(channel_id)
            if channel is None:
                continue
            if channel.flag == AnalogChannelFlag.ACC:
                currents.append(channel)
            elif channel.flag == AnalogChannelFlag.ACV:
                voltages.append(channel)

        if currents:
            return ACCBranch.from_analog_channels(currents)
        return ACVBranch.from_analog_channels(voltages) if voltages else ACVBranch()

    def get_status_channel_info(self, index: int) -> Optional[StatusChannel]:
        """
        根据 index 获取开关量通道

        参数:
            index(int): 通道索引
            
        返回:
            开关量通道，未找到返回 None
        """
        return self.status_channels.get(index)

    def __str__(self):
        """
        返回COMTRADE数据模型的XML字符串表示
        
        返回:
            格式化的XML字符串，包含完整的数据模型
        """
        parts = [super().__str__()]

        parts.extend(str(ana) for ana in self.analog_channels.values())
        parts.extend(str(sta) for sta in self.status_channels.values())
        parts.extend(str(bus) for bus in self.buses)
        parts.extend(str(line) for line in self.lines)
        parts.extend(str(trans) for trans in self.transformers)

        parts.append("</scl:ComtradeModel>")
        return "\n".join(parts)

    @classmethod
    def from_xml(cls, element: Element, ns: dict, cfg: Optional[Configure] = None) -> 'ComtradeModel':
        """
        从XML元素中解析数据模型

        参数:
            element: XML元素
            ns: 命名空间映射
            cfg: Configure对象，可选，用于在解析时传入analog和digital通道信息
            
        返回:
            ComtradeModel: 数据模型实例
        """
        if not ns or 'scl' not in ns or not isinstance(ns, dict):
            uri = None
            if isinstance(element.tag, str) and element.tag.startswith('{') and '}' in element.tag:
                uri = element.tag[1:element.tag.index('}')]
            ns = {'scl': uri} if uri else {'scl': 'http://www.iec.ch/61850/2003/SCL'}

        # 先解析模拟通道和开关量通道，以便后续解析时可以传入
        analog_channels = cls._find_analog_channels(element, ns, cfg)
        status_channels = cls._find_status_channels(element, ns, cfg)

        # Helper function to find elements with fallback
        def find_elements(tag_name: str, class_type) -> list:
            """查找并解析指定类型的元素"""
            _uri = ns.get('scl')
            elements = element.findall(f'scl:{tag_name}', ns)
            if not elements and _uri:
                elements = element.findall(f'.//{{{_uri}}}{tag_name}')

            if not hasattr(class_type, 'from_xml'):
                return []

            # 检查 from_xml 方法是否接受 analog_channels 或 status_channels 参数
            import inspect
            sig = inspect.signature(class_type.from_xml)
            params = sig.parameters

            kwargs = {}
            if 'analog_channels' in params:
                kwargs['analog_channels'] = analog_channels
            if 'status_channels' in params:
                kwargs['status_channels'] = status_channels

            if kwargs:
                return [class_type.from_xml(el, ns, **kwargs) for el in elements]
            return [class_type.from_xml(el, ns) for el in elements]

        def find_elements_as_dict(tag_name: str, class_type) -> dict:
            """查找并解析指定类型的元素为字典"""
            _uri = ns.get('scl')
            elements = element.findall(f'scl:{tag_name}', ns)
            if not elements and _uri:
                elements = element.findall(f'.//{{{_uri}}}{tag_name}')

            if not hasattr(class_type, 'from_xml'):
                return {}

            result = {}
            for el in elements:
                obj = class_type.from_xml(el, ns)
                result[obj.index] = obj
            return result

        # 先解析根元素属性，再解析设备列表
        base_model = ComtradeBaseModel.from_xml(element, ns)

        comtrade_model = ComtradeModel(
            station_name=base_model.station_name,
            version=base_model.version,
            rec_dev_name=base_model.rec_dev_name,
            xmlns_scl=base_model.xmlns_scl,
            xmlns_xsi=base_model.xmlns_xsi,
            xsi_schema_location=base_model.xsi_schema_location,
            reference=base_model.reference,
            buses=find_elements('Bus', Bus),
            lines=find_elements('Line', Line),
            transformers=find_elements('Transformer', Transformer),
            analog_channels=analog_channels,
            status_channels=status_channels
        )

        # 关联线路和母线
        comtrade_model._link_lines_to_buses()

        return comtrade_model

    @classmethod
    def _find_analog_channels(cls, element: Element, ns: dict, cfg: Optional[Configure] = None) -> dict:
        """查找并解析模拟通道为字典"""
        _uri = ns.get('scl')
        elements = element.findall(f'scl:AnalogChannel', ns)
        if not elements and _uri:
            elements = element.findall(f'.//{{{_uri}}}AnalogChannel')

        result = {}
        for el in elements:
            analog = None
            if cfg is not None:
                idx = int(el.get('idx_cfg', 1))
                analog = cfg.analogs.get(idx)
            obj = AnalogChannel.from_xml(el, analog)
            result[obj.index] = obj
        return result

    @classmethod
    def _find_status_channels(cls, element: Element, ns: dict, cfg: Optional[Configure] = None) -> dict:
        """查找并解析开关量通道为字典"""
        _uri = ns.get('scl')
        elements = element.findall(f'scl:StatusChannel', ns)
        if not elements and _uri:
            elements = element.findall(f'.//{{{_uri}}}StatusChannel')

        result = {}
        for el in elements:
            digital = None
            if cfg is not None:
                idx = int(el.get('idx_cfg', 1))
                digital = cfg.statuses.get(idx)
            obj = StatusChannel.from_xml(el, ns, digital)
            result[obj.index] = obj
        return result

    def _link_lines_to_buses(self):
        """
        关联线路和母线
        
        遍历所有线路，根据 bus_index 属性：
        - 如果 bus_index 为 0，则在 buses 中查找 v_rtg 相同的 Bus 对象
        - 如果 bus_index 不为 0，则在 buses 中查找 index 相同的 Bus 对象
        将找到的 Bus 对象添加到 line.buses 列表中
        """
        for line in self.lines:
            if line.bus_index == 0:
                # bus_index 为 0，查找 v_rtg 相同的 Bus
                for bus in self.buses:
                    if abs(bus.rated_primary_voltage - line.rated_primary_voltage) < 0.001:
                        line.buses.append(bus)
            else:
                # bus_index 不为 0，查找 index 相同的 Bus
                for bus in self.buses:
                    if bus.index == line.bus_index:
                        line.buses.append(bus)
                        break

    @classmethod
    def from_file(cls, file_name: Path | ComtradeFile | str, cfg: Optional[Configure] = None) -> 'ComtradeModel|None':
        """
        从文件路径中加载并解析数据模型

        参数:
            file_name: 文件路径，可以是Path对象、ComtradeFile对象或字符串路径
            cfg: Configure对象，可选，用于在解析时传入analog和digital通道信息
            
        返回:
            ComtradeModel: 数据模型实例，如果文件不存在或禁用则返回None
        """
        cf = ComtradeFile.from_path(file_path=file_name)

        if not cf.dmf_path.is_enabled():
            return None
        dmf_path = cf.dmf_path.path

        ns = {
            "ns": "http://www.iec.ch/61850/2003/SCL"
        }
        logging.debug(f"正在解析{dmf_path}")
        try:
            tree = ET.parse(dmf_path)
            root = tree.getroot()
            return ComtradeModel.from_xml(root, ns, cfg)
        except ET.ParseError as e:
            error_str = f"文件{dmf_path}解析错误,{str(e)}"
            logging.warning(error_str)
            raise ValueError(error_str)

    @classmethod
    def from_cfg(cls, cfg_obj: Configure) -> 'ComtradeModel':
        """
        从配置对象中创建数据模型

        将配置对象中的模拟量和数字量通道转换为DMF格式的通道对象。
        
        参数:
            cfg_obj: 配置对象，包含analogs和digitals通道信息
            
        返回:
            ComtradeModel: 数据模型实例，仅包含通道信息
        """
        _dmf = cls(station_name=cfg_obj.header.station,
                   rec_dev_name=cfg_obj.header.recorder)
        for analog in cfg_obj.analogs.values():
            analog_channel = AnalogChannel.from_analog(analog)
            _dmf.analog_channels[analog_channel.index] = analog_channel
        for digital in cfg_obj.statuses.values():
            digital_channel = StatusChannel.from_digital(digital)
            _dmf.status_channels[digital_channel.index] = digital_channel
        return _dmf

    def from_inf(self, inf_obj: Information):

        for bus in inf_obj.bus_sections:
            bus = Bus.from_bus_section(bus, self.analog_channels, self.status_channels)
            for _bus in self.buses:
                if _bus.__eq__(bus):
                    _bus.update(bus)
                    break
            else:
                self.buses.append(bus)
        for line in inf_obj.line_sections:
            pass
        for transformer in inf_obj.transformer_sections:
            pass

    def _edit_buses(self, bus: Bus):
        """
        添加母线对象到数据模型

        参数:
            bus: 母线对象
        """
        if self.buses is None:
            self.buses = [bus]
        else:
            for _bus in self.buses:
                if not _bus.__eq__(bus):
                    self.buses.append(bus)
                self.buses.append(bus)

    def write_file(self, output_file_path: ComtradeFile | Path | str):
        """
        将数据模型写入XML文件

        参数:
            output_file_path: 输出文件路径，可以是ComtradeFile对象、Path对象或字符串路径
        """
        output_file_path = ComtradeFile.from_path(output_file_path)
        dmf_path = output_file_path.dmf_path.path

        with open(dmf_path, "w", encoding="utf-8") as f:
            f.write(self.__str__())
        logging.info(f"数据模型文件{output_file_path}写入成功")
        return True


if __name__ == '__main__':
    dmf_file = r"D:\codeArea\comtrade\comtrade-io\data\hjz.dmf"
    dmf = ComtradeModel.from_file(dmf_file)
    print(dmf)
