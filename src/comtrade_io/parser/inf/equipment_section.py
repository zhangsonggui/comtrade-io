import re

from ...model.channel import Analog, Status
from ...model.equipment.equipment import Equipment
from ...utils import get_logger

logger = get_logger()


def parse_number_with_unit(s: str) -> float:
    """从带单位的字符串中提取数值

    例如 "10.5(km)" → 10.5, "220kV" → 220.0

    参数:
        s: 可能包含单位的数字字符串

    返回:
        float: 提取的数值，未匹配到数字时返回 0.0
    """
    match = re.search(r"\d+\.?\d*", s)
    return float(match.group()) if match else 0.0


def parse_four_values(s: str) -> list[float]:
    """解析逗号分隔的四元组数值

    例如 "0.01,0.1,0.03,0.3" → [0.01, 0.1, 0.03, 0.3]

    参数:
        s: 逗号分隔的四个数值

    返回:
        list[float]: 最多四个浮点数值
    """
    parts = s.split(",")
    return [parse_number_with_unit(p) for p in parts[:4]]


def parse_two_values(s: str) -> list[float]:
    """解析逗号分隔的二元组数值

    例如 "0.005,0.05" → [0.005, 0.05]

    参数:
        s: 逗号分隔的两个数值

    返回:
        list[float]: 最多两个浮点数值
    """
    parts = s.split(",")
    return [parse_number_with_unit(p) for p in parts[:2]]


def str2ids(string: str) -> list[int] | None:
    """
    将逗号分隔的字符串转换为整数ID列表

    Args:
        string: 逗号分隔的数字字符串，例如 "1,2,3"

    Returns:
        转换后的非零整数列表，如果输入为空或包含无效数字则返回 None

    Note:
        - 自动跳过空字符串和值为0的数字
        - 遇到无法转换为整数的内容时立即返回 None
    """
    if not string or not string.strip():
        return None

    parts = string.strip().split(",")
    result = []
    for part in parts:
        part = part.strip()
        if part:  # 跳过空字符串
            try:
                _id = int(part)
                if _id != 0:
                    if not result or _id > result[-1]:
                        result.append(_id)
            except ValueError:
                # 遇到无效数字时返回None或跳过，根据业务需求决定
                return None
    return result if result else None


def str2channel(string: str, channels: dict[int, Analog | Status]) -> list:
    """将逗号分隔的通道 ID 字符串转换为通道对象列表

    参数:
        string: 逗号分隔的数字字符串，如 "1,2,3"
        channels: 通道字典（按 index 索引）

    返回:
        list: 通道对象列表，找不到对应 ID 时跳过
    """
    ids = str2ids(string)
    return [channels.get(i) for i in ids if channels.get(i) is not None] if ids else []


class EquipmentSection:
    """设备部件基类

    提供从 INF 字典数据创建设备共性的方法：
    - 提取设备 index / uuid / 名称
    - 解析 TV_CHNS（电压通道引用）
    - 解析 TA_CHNS（电流通道引用）
    - 解析 STATUS_CHNS（开关量通道引用）
    """

    @classmethod
    def from_dict(
        cls,
        data: dict,
        analog_channels: dict[int, Analog],
        status_channels: dict[int, Status],
    ) -> Equipment:
        """从字典数据创建 Equipment 基类对象

        参数:
            data: 设备节键值对
            analog_channels: 模拟通道字典（用于解析 TV_CHNS / TA_CHNS 引用）
            status_channels: 开关量通道字典（用于解析 STATUS_CHNS 引用）

        返回:
            Equipment: 包含 index / uuid / name / acvs / accs / stas 的设备基类
        """
        index = data.get("index", None)
        uuid = data.get("SYS_ID", "")
        name_str = data.get("DEV_ID", data.get("Name", ""))
        if "," in name_str:
            _, name = name_str.split(",", 1)
        else:
            name = name_str
        if not name:
            name = f"Equipment_{index if index else 0}"
        voltages = str2channel(data.get("TV_CHNS", ""), analog_channels)
        currents = str2channel(data.get("TA_CHNS", ""), analog_channels)
        stas = str2channel(data.get("STATUS_CHNS", ""), status_channels)

        logger.debug(
            f"设备节解析: index={index}, name={name}, "
            f"电压通道={len(voltages)}, 电流通道={len(currents)}, 开关量通道={len(stas)}"
        )
        return Equipment(
            index=index, uuid=uuid, name=name, acvs=voltages, accs=currents, stas=stas
        )
