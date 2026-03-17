#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field


class InfInfo(BaseModel):
    """Inf information解析结果，兼容常见字段映射，保留原始键值对以便扩展。"""
    data: Dict[str, str] = Field(default_factory=dict, description="原始 Inf 字段字典")

    # 常见字段映射（可扩展）
    manufacturer: Optional[str] = Field(default=None, description="制造商")
    model: Optional[str] = Field(default=None, description="设备模型")
    serial_number: Optional[str] = Field(default=None, description="序列号")
    ct_ratio: Optional[str] = Field(default=None, description="CT 比值，例如 100/1")
    pt_ratio: Optional[str] = Field(default=None, description="PT 比值，例如 110/1")
    frequency: Optional[float] = Field(default=None, description="频率")
    sampling_rate: Optional[float] = Field(default=None, description="采样率")
    time_base: Optional[str] = Field(default=None, description="时间基准")
    clock_source: Optional[str] = Field(default=None, description="时钟源")
    software_version: Optional[str] = Field(default=None, description="软件版本")
    hardware_version: Optional[str] = Field(default=None, description="硬件版本")
    firmware_version: Optional[str] = Field(default=None, description="固件版本")
    time_reference: Optional[str] = Field(default=None, description="时间参考")

    # 额外字段，保留对未显式映射字段的兼容性
    extra: Dict[str, str] = Field(default_factory=dict, description="额外字段映射")

    @classmethod
    def from_file(cls, file_path: Path) -> 'InfInfo':
        """从 INF 文件解析信息，返回 InfInfo 实例"""
        if file_path is None:
            raise FileNotFoundError("文件路径为空")
        if not file_path.exists():
            raise FileNotFoundError(f"文件 {file_path.absolute()} 不存在")
        if not file_path.is_file():
            raise IsADirectoryError(f"{file_path.absolute()} 是目录，不是文件")

        parsed: Dict[str, str] = {}
        common_map = {
            'manufacturer'     : 'manufacturer',
            'vendor'           : 'manufacturer',
            'model'            : 'model',
            'device_model'     : 'model',
            'serial_number'    : 'serial_number',
            'serial'           : 'serial_number',
            'ct_ratio'         : 'ct_ratio',
            'ct_ratio_value'   : 'ct_ratio',
            'pt_ratio'         : 'pt_ratio',
            'pt_ratio_value'   : 'pt_ratio',
            'frequency'        : 'frequency',
            'nominal_frequency': 'frequency',
            'sampling_rate'    : 'sampling_rate',
            'sample_rate'      : 'sampling_rate',
            'samplingrate'     : 'sampling_rate',  # Added to handle SamplingRate without underscore
            'time_base'        : 'time_base',
            'clock_source'     : 'clock_source',
            'software_version' : 'software_version',
            'hardware_version' : 'hardware_version',
            'firmware_version' : 'firmware_version',
            'time_reference'   : 'time_reference',
        }

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith('#') or line.startswith('!') or line.startswith(';'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                elif ':' in line:
                    k, v = line.split(':', 1)
                else:
                    continue
                key = k.strip().lower().replace(' ', '_')
                val = v.strip()
                parsed[key] = val

        typed: Dict[str, object] = {}
        for key, val in parsed.items():
            if key in common_map:
                field = common_map[key]
                if field in {'frequency', 'sampling_rate'}:
                    # 尝试将数值字段转换为数字，遇到非数字保留字符串
                    try:
                        if '/' in val:
                            # 比如 '100/1' 这类比值直接保留为字符串
                            typed[field] = val
                        else:
                            typed[field] = float(val) if ('.' in val or 'e' in val.lower()) else int(val)
                    except Exception:
                        typed[field] = val
                else:
                    typed[field] = val

        info = cls(
            data=parsed,
            manufacturer=typed.get('manufacturer'),
            model=typed.get('model'),
            serial_number=typed.get('serial_number'),
            ct_ratio=typed.get('ct_ratio'),
            pt_ratio=typed.get('pt_ratio'),
            frequency=typed.get('frequency'),
            sampling_rate=typed.get('sampling_rate'),
            time_base=typed.get('time_base'),
            clock_source=typed.get('clock_source'),
            software_version=typed.get('software_version'),
            hardware_version=typed.get('hardware_version'),
            firmware_version=typed.get('firmware_version'),
            time_reference=typed.get('time_reference'),
            extra={k: v for k, v in parsed.items() if k not in common_map}
        )
        return info
