#!/usr/bin/env python
# -*- coding: utf-8 -*-
from xml.etree.ElementTree import Element

from comtrade_io.base.description import Description
from comtrade_io.utils import parse_float


class DescriptionElement:
    """
    描述元素
    """

    @classmethod
    def from_xml(cls, element: Element, ns: dict) -> Description:
        """
        从XML元素创建ComtradeBaseModel实例

        参数:
            element: XML元素
            ns: 命名空间

        返回:
            ComtradeBaseModel实例
        """
        return Description(
                station_name=element.get('station_name', ''),
                data_model_version=parse_float(element.get('version', '1.0')),
                rec_dev_name=element.get('rec_dev_name', ''),
                xmlns_scl=element.get('xmlns:scl', 'http://www.iec.ch/61850/2003/SCL'),
                xmlns_xsi=element.get('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance'),
                xsi_schema_location=element.get('xsi:schemaLocation',
                                                'http://www.iec.ch/61850/2003/SCLcomtrade_mdl_v1.1.xsd')
        )
