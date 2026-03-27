#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pydantic import Field

from comtrade_io.cfg.cfg_channel_model import CfgChannelBaseModel
from comtrade_io.type import TranSide, Unit
from comtrade_io.utils import get_logger, parse_float

logging = get_logger()


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


class Analog(CfgChannelBaseModel):
    """
    cfg文件中模拟量通道类

    参数:
        index(int): 通道索引（模拟通道是An，数字通道是Dn，统一用index表示）
        name(str): 通道标识（ch_id）
        phase(Phase): 通道相别标识（ph）
        equip(str): 被监视的电路元件（ccbm）
        unit(Unit): 通道单位
        multiplier(float): 通道增益系数(实数,可使用标准浮点标记法)
        offset(float): 通道偏移量
        delay(float): 通道时滞（μs）
        min_value(float): 数值最小值
        max_value(float): 数值最大值
        primary(float): 互感器一次系数
        secondary(float): 互感器二次系数
        tran_side(TranSide): 转换标识(P/S)
    """
    unit: Unit = Field(default=Unit.NONE, description="通道单位")
    multiplier: float = Field(default=1.0, ge=0.0, description="通道增益系数(实数,可使用标准浮点标记法)")
    offset: float = Field(default=0.0, description="通道偏移量")
    delay: float = Field(default=0.0, description="通道时滞（μs）")
    min_value: float = Field(default=0.0, description="数值最小值")
    max_value: float = Field(default=0.0, description="数值最大值")
    primary: float = Field(default=1.0, description="互感器一次系数")
    secondary: float = Field(default=1.0, description="互感器二次系数")
    tran_side: TranSide = Field(default=TranSide.S, description="转换标识(P/S)")

    def __str__(self):
        """
        返回对象的字符串表示形式

        该方法扩展了父类的__str__方法，在其基础上添加了当前对象的特定属性信息，
        包括单位值、添加标志、偏移量、延迟、最小值、最大值、主次标识和传输侧等信息。

        Returns:
            str: 包含父类字符串表示和当前对象所有属性信息的完整字符串
        """
        return (
                super().__str__()
                + f",{self.unit.value},{self.multiplier},{self.offset},{self.delay}"
                + f",{self.min_value},{self.max_value},{self.primary},{self.secondary}"
                + f",{self.tran_side.value}"
        )

    def to_information(self):
        """
        返回对象的信息字符串表示形式
        包括通道标识、通道名称、参引路径、单位、通道增益系数、通道偏移系数、通道延时、
        最小值、最大值、一次变比系数、二次变比系数、数据标识。

        Returns:
            str: 模拟量通道信息字符串表示形式
        """
        attrs = [
            f"[Public Analog_Channel_#{self.index}]",
            f'Channel_ID="{self.name}"',
            f'Phase_ID="{self.phase.value}"',
            f'Monitored_Component=""',
            f'Channel_Units="{self.unit.value}"',
            f'Channel_Multiplier="{self.multiplier}"',
            f'Channel_Offset="{self.offset}"',
            f'Channel_Skew="{self.delay}"',
            f'Range_Minimum_Limit_Value="{self.min_value}"',
            f'Range_Maximum_Limit_Value="{self.max_value}"',
            f'Channel_Ratio_Primary="{self.primary}"',
            f'Channel_Ratio_Secondary="{self.secondary}"',
            f'Data_Primary_Secondary="{self.tran_side.value}"'
        ]
        return "\n".join(attrs)

    @classmethod
    def from_str(cls, _str: str) -> 'Analog':
        """从逗号分隔的字符串反序列化模拟量对象

        将配置文件中的模拟量通道字符串解析为Analog对象。
        该方法会自动处理通道名称中可能存在的非法逗号问题。

        参数:
            _str: 逗号分隔的模拟量通道字符串

        Returns:
            Analog: 解析后的模拟量通道对象

        异常:
            ValueError: 当字符串格式不正确或通道名称包含非法逗号时抛出
        """
        str_arr = _str.strip().split(',')
        if len(str_arr) > 13:
            str_arr = amend_channel_name_error(str_arr)
            logging.warning(f"{_str}参数超过规范的长度，怀疑ch_id(name)存在不合法的“,”,已尝试消除")
            if not str_arr:
                logging.error(f"{_str}参数存在不合法的“,”，尝试合并失败，请检查")
                raise ValueError(f"{_str}参数存在不合法的“,”，尝试合并失败，请检查")
        channel = super().from_str(','.join(str_arr[:4]))
        analog_dict = channel.model_dump()
        analog_dict['unit'] = Unit.from_value(str_arr[4], Unit.NONE)
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
