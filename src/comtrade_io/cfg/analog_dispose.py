#!/usr/bin/env python
# -*- coding: utf-8 -*-
from comtrade_io.channel.analog import Analog
from comtrade_io.channel.channel import ChannelBaseModel
from comtrade_io.type import TranSide, Unit
from comtrade_io.utils import get_logger, parse_float

logging = get_logger()

UNIT_PREFIXES = ('T', 'G', 'M', 'k', '', 'm', 'u', 'n', 'p')


def _parse_unit_and_multiplier(unit_str: str):
    """解析单位字符串，分离乘数和基本单位

    支持:
      - 合并格式: "kV", "mA", "MHz" 等
      - 分开格式: 单位="V", multiplier="k"

    参数:
        unit_str: 单位字符串，如 "kV", "V" 等

    返回:
        tuple: (Unit枚举, 乘数字符串)
    """
    unit_str = unit_str.strip()
    if not unit_str:
        return Unit.NONE, ''

    # 尝试匹配合并格式 (如 kV, mA)
    for prefix in UNIT_PREFIXES:
        if prefix and unit_str.startswith(prefix):
            base_part = unit_str[len(prefix):]
            combined = prefix + base_part
            unit_enum = Unit.get_member_by_value(combined)
            if unit_enum:
                return unit_enum, prefix

    # 无法分离，尝试直接匹配
    unit_enum = Unit.get_member_by_value(unit_str)
    if unit_enum:
        return unit_enum, unit_enum.multiplier.value

    return Unit.NONE, ''


def amend_channel_name_error(_channel_arr: list) -> list:
    """
    cfg文件通道信息依赖英文逗号进行分割数据
    通道名称依赖人工录入，在部分录波设备中人员可能错误录入非法"，"
    本函数通过检测第五位索引增益系数是否是数字或第四位索引是否为单位来合并名称中包含的逗号
    :param _channel_arr: 分割后的通道信息列表
    :return: 合并后的通道信息列表
    """
    for i in range(5, len(_channel_arr)):
        try:
            parse_float(_channel_arr[i])
            al_new = [_channel_arr[0], '_'.join(_channel_arr[2:i - 3])]
            al_new.extend(_channel_arr[i - 3:])
            return al_new
        except ValueError:
            continue
    return []


class AnalogDispose:
    """
    模拟量数据处理类
    """

    @staticmethod
    def from_string(_str: str):
        """
        从字符串中解析模拟量数据
        """
        str_arr = _str.strip().split(',')
        if len(str_arr) > 13:
            str_arr = amend_channel_name_error(str_arr)
            logging.warning(f"{_str}参数超过规范的长度，怀疑ch_id(name)存在不合法的", ",已尝试消除")
            if not str_arr:
                logging.error(f"{_str}参数存在不合法的", "，尝试合并失败，请检查")
                raise ValueError(f"{_str}参数存在不合法的", "，尝试合并失败，请检查")
        channel = ChannelBaseModel.from_str(','.join(str_arr[:4]))
        analog_dict = channel.model_dump()
        unit_obj, multiplier_prefix = _parse_unit_and_multiplier(str_arr[4])
        analog_dict['unit'] = unit_obj
        analog_dict['unit_multiplier'] = multiplier_prefix if multiplier_prefix else None
        analog_dict['multiplier'] = parse_float(str_arr[5], 1.0)
        analog_dict['offset'] = parse_float(str_arr[6], 0.0)
        analog_dict['delay'] = parse_float(str_arr[7], 0.0)
        analog_dict['min_value'] = parse_float(str_arr[8], 0.0)
        analog_dict['max_value'] = parse_float(str_arr[9], 0.0)
        if len(str_arr) > 11:
            primary = parse_float(str_arr[10])
            secondary = parse_float(str_arr[11])
            analog_dict['primary'] = primary if primary != 0 else 1.0
            analog_dict['secondary'] = secondary if secondary != 0 else 1.0
        analog_dict['tran_side'] = TranSide.from_value(str_arr[12], TranSide.S) if len(str_arr) > 12 else TranSide.S
        return Analog(**analog_dict)