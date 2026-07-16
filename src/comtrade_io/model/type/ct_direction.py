from .base_enum import BaseEnum


class CtDirection(BaseEnum):
    """电流互感器极性方向枚举

    定义电流互感器(CT)的极性方向。
    """

    POS = ("pos", "正向")
    NEG = ("neg", "反向")
    UNC = ("unc", "未知")
