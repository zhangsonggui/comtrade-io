#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from comtrade_io.base.description import Description
from comtrade_io.channel import Analog, Status
from comtrade_io.comtrade_file import ComtradeFile
from comtrade_io.equipment import Bus, Line, Transformer
from comtrade_io.equipment.branch import ACVBranch
from comtrade_io.equipment.equipment_group import EquipmentGroup
from comtrade_io.inf.analog_section import AnalogSection
from comtrade_io.inf.bus_section import BusSection
from comtrade_io.inf.description_section import DescriptionSection
from comtrade_io.inf.line_section import LineSection
from comtrade_io.inf.status_section import StatusSection
from comtrade_io.inf.transformer_section import TransformerSection
from comtrade_io.utils import get_logger

logging = get_logger()


def parse_section_header(header_str: str):
    # 验证方括号格式
    bracket_match = re.match(r'^\[([^\]]+)\]$', header_str)
    if not bracket_match:
        return None

    content = bracket_match.group(1).strip()

    # 按空格分割，提取 area
    space_parts = content.split(' ', 1)
    if len(space_parts) < 2:
        return None

    area = space_parts[0]
    rest = space_parts[1]

    # 按 _# 分割 type 和 index
    hash_match = re.match(r'^(.+?)_#(\d+)$', rest)
    if hash_match:
        section_type = hash_match.group(1)
        index = int(hash_match.group(2))
    else:
        # 无法识别_#，整个作为type，index为0
        section_type = rest
        index = 0

    return {'area': area, 'type': section_type, 'index': index}


class Information(BaseModel):
    """INF文件解析和序列化主类"""
    record_info: Optional[list] = Field(default_factory=list, description="录波记录信息")
    file_description: Optional[Description] = Field(default_factory=Description, description="文件描述信息")
    analog_channels: Optional[dict[int, Analog]] = Field(default_factory=dict, description="模拟通道信息")
    status_channels: Optional[dict[int, Status]] = Field(default_factory=dict, description="状态量通道信息")
    analog_channel_parameters: Optional[dict[int, Analog]] = Field(
        default_factory=dict, description="模拟通道参数信息"
    )
    status_channel_parameters: Optional[dict[int, Status]] = Field(
        default_factory=dict, description="状态量通道参数信息"
    )
    buses: Optional[list[Bus]] = Field(default_factory=list, description="母线信息")
    lines: Optional[list[Line]] = Field(default_factory=list, description="线路信息")
    transformers: Optional[list[Transformer]] = Field(default_factory=list, description="变压器信息")
    channels_group: Optional[list] = Field(default_factory=list, description="通道组信息")

    def _get_voltage_from_channel(self, channels: list[Analog]) -> tuple[int, list[Bus]]:
        """
        根据模拟量通道列表找到对应的母线对象

        Args:
            channels: 模拟量通道列表

        Returns:
            匹配的母线对象列表
        """
        matched_buses = []

        for channel in channels:
            for bus in self.buses:
                voltage_ids = [chn.index for chn in bus.acvs]
                if channel.index in voltage_ids:
                    if bus not in matched_buses:
                        matched_buses.append(bus)
                    break
        bus_id = 0
        if len(matched_buses) == 1:
            bus_id = matched_buses[0].index

        return bus_id, matched_buses

    def _parse_analog_channel_parameters(self, data: dict):
        """解析模拟量通道参数段 [ZYHD ANALOG_CHANNELS_Parameter]"""
        for key, value in data.items():
            if not key.upper().startswith("CHNL_INFO_#"):
                continue
            if not value:
                continue
            parts = [p.strip() for p in value.split(",")]
            if len(parts) < 11:
                continue

            def get_part(idx, default=None):
                return parts[idx] if idx < len(parts) else default

            def to_float_part(idx, default=0.0):
                val = get_part(idx, None)
                if val is None or val == "":
                    return default
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return default

            try:
                idx_cfg = int(parts[0])
            except (ValueError, TypeError):
                continue

            param_data = {
                "index": idx_cfg,
                "idx_org": int(parts[1]) if parts[1] else 0,
                "name": parts[2],
                "type": parts[3],
                "freq": to_float_part(4, 50.0),
                "t1": to_float_part(5, 0.0),
                "t2": to_float_part(7, 0.0),
                "ad": to_float_part(9, 0.0),
                "bd": to_float_part(10, 0.0),
            }

            param_obj = AnalogSection.from_dict(param_data)
            self.analog_channel_parameters[idx_cfg] = param_obj

            # 如果已有对应通道，合并参数
            if idx_cfg in self.analog_channels:
                existing = self.analog_channels[idx_cfg]
                if param_obj.primary != 1.0:
                    existing.primary = param_obj.primary
                if param_obj.secondary != 1.0:
                    existing.secondary = param_obj.secondary
                if param_obj.freq != 50.0:
                    existing.freq = param_obj.freq
                if param_obj.au is not None:
                    existing.au = param_obj.au
                if param_obj.bu is not None:
                    existing.bu = param_obj.bu
                if param_obj.flag is not None:
                    existing.flag = param_obj.flag
                if param_obj.type is not None:
                    existing.type = param_obj.type
            else:
                self.analog_channels[idx_cfg] = param_obj

    def _parse_status_channel_parameters(self, data: dict):
        """解析开关量通道参数段 [ZYHD STATUS_CHANNELS_Parameter]"""
        for key, value in data.items():
            if not key.upper().startswith("CHNL_INFO_#"):
                continue
            if not value:
                continue
            parts = [p.strip() for p in value.split(",")]
            if len(parts) < 5:
                continue

            def get_part(idx, default=None):
                return parts[idx] if idx < len(parts) else default

            try:
                idx_cfg = int(parts[0])
            except (ValueError, TypeError):
                continue

            param_data = {
                "index": idx_cfg,
                "idx_org": int(parts[1]) if parts[1] else 0,
                "name": parts[2],
                "level": parts[3],
                "type": parts[4],
                "obj": get_part(5),
            }

            param_obj = StatusSection.from_dict(param_data)
            self.status_channel_parameters[idx_cfg] = param_obj

            # 如果已有对应通道，合并参数
            if idx_cfg in self.status_channels:
                existing = self.status_channels[idx_cfg]
                if param_obj.flag is not None:
                    existing.flag = param_obj.flag
                if param_obj.type is not None:
                    existing.type = param_obj.type
                if param_obj.equipment_no is not None:
                    existing.equipment_no = param_obj.equipment_no
            else:
                self.status_channels[idx_cfg] = param_obj

    @classmethod
    def from_file(cls, file_name: str | Path) -> 'EquipmentGroup | None':
        """从文件读取并解析INF内容，返回 EquipmentGroup 实例"""
        cf = ComtradeFile.from_path(file_name)
        if not cf.inf_path.is_enabled():
            return None
        inf_path = cf.inf_path.path
        logging.debug(f"开始解析INF文件: {inf_path}")
        try:
            inf_content = inf_path.read_text(encoding='gbk', errors='replace')
        except UnicodeDecodeError:
            logging.warning(f"配置文件{inf_path}编码不是GBK编码，尝试使用UTF8解析")
            try:
                inf_content = inf_path.read_text(encoding="utf-8", errors='replace')
            except UnicodeDecodeError:
                logging.error(f"无法解析INF文件: {inf_path}")
                return None
        return cls.from_str(inf_content)

    @classmethod
    def from_str(cls, content: str) -> 'EquipmentGroup':
        """从字符串解析INF内容，返回 ComtradeModel 实例"""
        inst = cls()
        inst.split_sections(content)
        _model = EquipmentGroup()

        # 解析模拟通道（Analogs）直接使用已有对象
        _model.description = inst.file_description if hasattr(inst, 'file_description') else Description()
        _model.analogs = inst.analog_channels if hasattr(inst, 'analog_channels') else {}
        # 状态通道
        _model.statuses = inst.status_channels if hasattr(inst, 'status_channels') else {}
        _model.buses = inst.buses if hasattr(inst, 'buses') else []
        _model.lines = inst.lines if hasattr(inst, 'lines') else []
        _model.transformers = inst.transformers if hasattr(inst, 'transformers') else []

        return _model

    def split_sections(self, content: str):
        """将INF内容按节分割并将信息映射到对象字段"""
        current_section: list[str] = []

        def _process_section(section_lines: list[str]):
            """处理一个完整的节数据"""
            if not section_lines:
                return

            _header = section_lines[0]
            _parsed = parse_section_header(_header)
            if not _parsed:
                return

            sec_type = _parsed.get('type', '').upper()
            data = {k: v for k, v in _kv_pairs(section_lines).items()}

            # 添加index信息（如果存在）
            if 'index' in _parsed:
                data['index'] = _parsed['index']

            # 根据节类型分发到对应的列表
            if sec_type in ['RECORD_INFO', 'RECORD_INFORMATION']:
                self.record_info.append(data)
            elif sec_type in ['FILE_DESCRIPTION']:
                self.file_description = DescriptionSection.from_dict(data)
            elif sec_type in ['ANALOG_CHANNEL', 'ANALOG_CHANNELS']:
                ana = AnalogSection.from_dict(data)
                self.analog_channels[ana.index] = ana
            elif sec_type == "ANALOG_CHANNELS_PARAMETER":
                self._parse_analog_channel_parameters(data)
            elif sec_type in ['STATUS_CHANNEL', 'STATUS_CHANNELS']:
                sta = StatusSection.from_dict(data)
                self.status_channels[sta.index] = sta
            elif sec_type == "STATUS_CHANNELS_PARAMETER":
                self._parse_status_channel_parameters(data)
            elif sec_type == 'BUS':
                _bus = BusSection.from_dict(data, self.analog_channels, self.status_channels)
                _bus.voltage = ACVBranch.from_analog_channels(_bus.acvs)
                self.buses.append(_bus)
            elif sec_type == 'LINE':
                _line = LineSection.from_dict(data, self.analog_channels, self.status_channels)
                _line.bus_index, _line.buses = self._get_voltage_from_channel(_line.acvs)
                self.lines.append(_line)
            elif sec_type == 'TRANSFORMER':
                self.transformers.append(
                        TransformerSection.from_dict(data, self.analog_channels, self.status_channels))

        for line in content.splitlines():
            stripped_line = line.strip()
            # 新节头：保存上一个节的数据并重置
            if stripped_line.startswith('[') and stripped_line.endswith(']'):
                # 处理前一个节
                _process_section(current_section)
                # 开始新的节
                current_section = [stripped_line]
            else:
                current_section.append(stripped_line)

        # 处理最后一个节
        _process_section(current_section)


# 内部小工具：将区块文本行转为键值对字典
def _kv_pairs(lines: list[str]) -> dict:
    result: dict = {}
    for ln in lines:
        if '=' in ln:
            k, v = ln.split('=', 1)
            result[k.strip()] = v.strip()
    return result


if __name__ == '__main__':
    inf_file = r"D:\codeArea\Git_Work\comtrade\comtrade-io\example\data\20190413-023734.#0006BC1A.inf"
    model = Information.from_file(file_name=inf_file)
    try:
        # ComtradeModel 使用 dict 风格输出
        print(model.model_dump(indent=4))  # type: ignore[arg-type]
    except Exception:
        print(model)  # fallback
