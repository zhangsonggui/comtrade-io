#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMF元素模块

定义DMF数据模型的主类DMFElement，用于表示完整的电力系统数据模型。
该模型包含母线、线路、变压器等设备，以及模拟量和开关量通道。
支持从XML文件读取、解析和写入数据模型。
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.etree.ElementTree import Element

from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.dmf.analog_element import AnalogElement
from comtrade_io.dmf.bus_element import BusElement
from comtrade_io.dmf.description_element import DescriptionElement
from comtrade_io.dmf.line_element import LineElement
from comtrade_io.dmf.status_element import StatusElement
from comtrade_io.dmf.transformer_element import TransformerElement
from comtrade_io.equipment.equipment_group import EquipmentGroup
from comtrade_io.utils import get_logger

logging = get_logger(__name__)


class DmfElement(EquipmentGroup):

    @classmethod
    def from_xml(cls, element: Element, ns: dict) -> 'DmfElement':
        """
        从XML元素中解析数据模型

        参数:
            element: XML元素
            ns: 命名空间映射
        返回:
            DMFElement: 数据模型实例
        """
        if not ns or 'scl' not in ns or not isinstance(ns, dict):
            uri = None
            if isinstance(element.tag, str) and element.tag.startswith('{') and '}' in element.tag:
                uri = element.tag[1:element.tag.index('}')]
            ns = {'scl': uri} if uri else {'scl': 'http://www.iec.ch/61850/2003/SCL'}

        # 先解析模拟通道和开关量通道，以便后续解析时可以传入
        analog_channels = cls._find_channels(element, ns, "AnalogChannel")
        status_channels = cls._find_channels(element, ns, "StatusChannel")

        def find_elements(tag_name: str, element_class) -> list:
            """查找并解析指定类型的元素"""
            elements = cls._find_all_elements(element, ns, tag_name)
            if not hasattr(element_class, 'from_xml'):
                return []
            # 使用element类解析XML元素
            return [element_class.from_xml(el, ns, analog_channels, status_channels) for el in elements]

        dmf_element = cls(
                description=DescriptionElement.from_xml(element, ns),
                buses=find_elements('Bus', BusElement),
                lines=find_elements('Line', LineElement),
                transformers=find_elements('Transformer', TransformerElement),
                analogs=analog_channels,
                statuses=status_channels
        )

        # 关联线路和母线
        dmf_element._link_lines_to_buses()

        return dmf_element

    @classmethod
    def _find_all_elements(cls, parent: Element, ns: dict, tag_name: str) -> list:
        """
        使用多种方式查找XML元素

        参数:
            parent: 父XML元素
            ns: 命名空间映射
            tag_name: 标签名称
        返回:
            找到的XML元素列表
        """
        elements = []
        # 尝试多种方式查找元素
        if 'scl' in ns:
            elements = parent.findall(f'scl:{tag_name}', ns)
        if not elements and 'ns' in ns:
            elements = parent.findall(f'ns:{tag_name}', ns)
        if not elements:
            # 尝试使用命名空间URI直接查找
            for prefix, uri in ns.items():
                if uri:
                    elements = parent.findall(f'.//{{{uri}}}{tag_name}')
                    if elements:
                        break
        if not elements:
            # 尝试不带前缀
            elements = parent.findall(f'.//{tag_name}')
        return elements

    @classmethod
    def _find_channels(cls, element: Element, ns: dict, channel_type: str = "AnalogChannel") -> dict:
        """查找并解析通道为字典"""
        elements = cls._find_all_elements(element, ns, channel_type)
        result = {}
        for el in elements:
            if channel_type == "AnalogChannel":
                obj = AnalogElement.from_xml(el)
            else:
                obj = StatusElement.from_xml(el)
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
    def from_file(cls, file_name: Path | ComtradeFile | str) -> 'EquipmentGroup|None':
        """
        从文件路径中加载并解析数据模型

        参数:
            file_name: 文件路径，可以是Path对象、ComtradeFile对象或字符串路径

        返回:
            ComtradeModel: 数据模型实例，如果文件不存在或禁用则返回None
        """
        cf = ComtradeFile.from_path(file_path=file_name)

        if not cf.dmf_path.is_enabled():
            return None
        dmf_path = cf.dmf_path.path

        ns = {
            "scl": "http://www.iec.ch/61850/2003/SCL"
        }
        logging.debug(f"正在解析{dmf_path}")
        try:
            tree = ET.parse(dmf_path)
            root = tree.getroot()
            _dmf = cls.from_xml(root, ns)
            return EquipmentGroup(
                    description=_dmf.description,
                    buses=_dmf.buses,
                    lines=_dmf.lines,
                    transformers=_dmf.transformers,
                    analogs=_dmf.analogs,
                    statuses=_dmf.statuses
            )
        except ET.ParseError as e:
            error_str = f"文件{dmf_path}解析错误,{str(e)}"
            logging.warning(error_str)
            return None


if __name__ == '__main__':
    file_name = r"D:\codeArea\Git_Work\comtrade\comtrade-io\example\data\GHBZ_220kV线路故障_20230512_194525.dmf"
    dmf = DmfElement.from_file(file_name)
    print(dmf)
