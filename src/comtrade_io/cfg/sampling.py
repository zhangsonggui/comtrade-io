#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""采样信息模型
描述：用于描述波形的采样信息，包含频率和采样段列表 nrates。"""
import json
from typing import List, Optional

from pydantic import BaseModel, Field

from comtrade_io.cfg.nrate import Nrate
from comtrade_io.utils import get_logger

logging = get_logger()


class Sampling(BaseModel):
    freq: Optional[float] = Field(default=50.0, description="电网频率")
    nrates: List[Nrate] = Field(default_factory=list, description="采样段")

    def __str__(self) -> str:
        """序列化为多行文本

        将采样信息对象转换为COMTRADE配置文件格式的多行字符串。
        第一行为采样频率，后续行为各采样段信息。

        Returns:
            str: 多行字符串，第一行为频率，后续行为NRATE行
        """
        freq_str = f"{self.freq}"
        nrate_size = len(self.nrates)
        nrates_str = '\n'.join([str(nrate) for nrate in self.nrates])
        if nrates_str:
            return f"{freq_str}\n{nrate_size}\n{nrates_str}"
        return freq_str

    def add_nrate(self, nrate: Nrate) -> None:
        """向采样段列表添加一个Nrate

        添加采样段并自动归一化端点以兼容相对/绝对端点的写法。
        如果端点值小于等于前一个端点，则视为相对长度；否则视为绝对端点。

        参数:
            nrate: 要添加的Nrate对象

        异常:
            ValueError: 当nrate不是Nrate实例时抛出
        """
        if not isinstance(nrate, Nrate):
            err_str = f"nrate 必须是 Nrate 实例"
            logging.error(err_str)
            raise ValueError(err_str)
        self.nrates.append(nrate)
        self._normalize_nrates()

    def _normalize_nrates(self) -> None:
        """将nrates中的end_point归一化为绝对端点

        内部方法，将所有采样段的结束点转换为绝对坐标：
        - 如果end_point > 上一个end_point，则保持为绝对端点
        - 否则将其视为相对长度，转换为 prev_end + end_point
        """
        prev_end = 0
        for nr in self.nrates:
            end_val = int(nr.end_point)
            if end_val <= prev_end:
                end_abs = prev_end + end_val
            else:
                end_abs = end_val
            nr.end_point = end_abs
            prev_end = end_abs

    @classmethod
    def from_str(cls, _str: str) -> 'Sampling':
        """从多行字符串反序列化采样信息

        将配置文件中的采样信息字符串解析为Sampling对象。
        第一行为采样频率，后续每行为一个NRATE采样段。
        支持仅包含频率一行的情况（nrates为空）。

        参数:
            _str: 多行字符串，第一行为频率，后续行为NRATE行

        Returns:
            Sampling: 解析后的采样信息对象
        """
        if not _str or _str.strip() == '':
            return cls()
        lines = [ln.strip() for ln in _str.strip().splitlines() if ln.strip() != '']
        if len(lines) == 0:
            return cls()
        freq = float(lines[0]) if lines[0] != '' else 0.0
        nrates: List[Nrate] = []
        for line in lines[2:]:
            if line:
                nrates.append(Nrate.from_str(line))
        s = cls(freq=freq, nrates=nrates)
        s._normalize_nrates()
        return s

    @classmethod
    def from_dict(cls, data: dict) -> 'Sampling':
        freq = data.get("freq", 50.0)
        nrates_data = data.get("nrates", [])
        nrates: List[Nrate] = []
        for item in nrates_data:
            if isinstance(item, dict):
                nrates.append(Nrate.from_dict(item))
            elif isinstance(item, str):
                nrates.append(Nrate.from_str(item))
            else:
                raise ValueError("非法的 nrates 元素类型")
        s = cls(freq=freq, nrates=nrates)
        s._normalize_nrates()
        return s

    @classmethod
    def from_json(cls, json_str: str) -> 'Sampling':
        data = json.loads(json_str)
        return cls.from_dict(data)
