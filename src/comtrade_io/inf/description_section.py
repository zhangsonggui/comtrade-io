#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.base.description import Description
from comtrade_io.type import Version


class DescriptionSection:
    """描述文件"""

    @classmethod
    def from_dict(cls, data: dict) -> Description:
        """
        从字典创建描述文件对象

        参数:
            data: 字典数据

        返回:
            Description: 描述文件对象
        """
        version_str = data.get('Revision_Year', '1991')
        return Description(
                station_name=data.get('Station_Name', ''),
                rec_dev_name=data.get('Recording_Device_ID', ''),
                version=Version.from_value(version_str)
        )
