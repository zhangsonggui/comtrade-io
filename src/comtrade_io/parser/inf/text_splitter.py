import re
from dataclasses import dataclass, field
from typing import Optional

from ...utils import get_logger

logger = get_logger()

# INF 节类型到 SectionData 属性名的映射
_SECTION_TYPES_MAP = {
    "FILE_DESCRIPTION": "file_description",
    "ANALOG_CHANNEL": "analog_channels",
    "ANALOG_CHANNELS": "analog_channels",
    "ANALOG_CHANNELS_PARAMETER": "analog_params_data",
    "STATUS_CHANNEL": "status_channels",
    "STATUS_CHANNELS": "status_channels",
    "STATUS_CHANNELS_PARAMETER": "status_params_data",
    "BUS": "buses",
    "LINE": "lines",
    "TRANSFORMER": "transformers",
}


@dataclass
class SectionData:
    """INF 节数据容器

    由 split_sections() 返回，存储 INF 文本中各节的原始键值对数据。
    不包含任何模型对象，仅作为 Builder 模块的输入。
    """

    file_description: Optional[dict] = None
    analog_channels: list[dict] = field(default_factory=list)
    analog_params_data: Optional[dict] = None
    status_channels: list[dict] = field(default_factory=list)
    status_params_data: Optional[dict] = None
    buses: list[dict] = field(default_factory=list)
    lines: list[dict] = field(default_factory=list)
    transformers: list[dict] = field(default_factory=list)


def parse_section_header(header_str: str) -> dict | None:
    """解析 INF 节头字符串

    格式示例:
        [Public Analog_Channel_#1] → {area: Public, type: Analog_Channel, index: 1}
        [Public Record_Information] → {area: Public, type: Record_Information, index: 0}

    参数:
        header_str: 节头字符串，如 "[ZYHD Bus_#2]"

    返回:
        dict | None: 包含 area / type / index 的字典，解析失败返回 None
    """
    bracket_match = re.match(r"^\[([^\]]+)\]$", header_str)
    if not bracket_match:
        return None

    content = bracket_match.group(1).strip()
    space_parts = content.split(" ", 1)
    if len(space_parts) < 2:
        return None

    area = space_parts[0]
    rest = space_parts[1]

    hash_match = re.match(r"^(.+?)_#(\d+)$", rest)
    if hash_match:
        section_type = hash_match.group(1)
        index = int(hash_match.group(2))
    else:
        section_type = rest
        index = 0

    return {"area": area, "type": section_type, "index": index}


def _kv_pairs(lines: list[str]) -> dict:
    """从节的行列表中提取键值对

    遍历行，提取包含 "=" 的行，分割为 key 和 value 并去除首尾空白。

    参数:
        lines: 节内的行列表，首行为节头，其余为键值行

    返回:
        dict: 键值对字典，不含节头
    """
    result: dict = {}
    for ln in lines:
        if "=" in ln:
            k, v = ln.split("=", 1)
            result[k.strip()] = v.strip()
    return result


def split_sections(content: str) -> SectionData:
    """将 INF 文本拆分为原始节数据

    逐行扫描文本，按节头分组，将每组行提取为键值对后按类型存入 SectionData。
    参数段数据在返回前会应用到对应的通道数据上。

    参数:
        content: INF 文件完整文本内容

    返回:
        SectionData: 包含所有节原始数据的容器对象
    """
    sections = SectionData()
    current_section: list[str] = []

    def _classify_and_store(lines: list[str]):
        """将一组行归类存储到 SectionData 中"""
        if not lines:
            return
        header = lines[0]
        parsed = parse_section_header(header)
        if not parsed:
            return

        sec_type = parsed.get("type", "").upper()
        data = _kv_pairs(lines)
        if "index" in parsed:
            data["index"] = parsed["index"]

        target_key = _SECTION_TYPES_MAP.get(sec_type)
        if target_key is None:
            return

        if target_key in (
            "file_description",
            "analog_params_data",
            "status_params_data",
        ):
            setattr(sections, target_key, data)
        else:
            getattr(sections, target_key).append(data)

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            _classify_and_store(current_section)
            current_section = [stripped]
        else:
            current_section.append(stripped)
    _classify_and_store(current_section)

    logger.debug(
        f"INF文本解析完成: {len(sections.analog_channels)}个模拟通道, "
        f"{len(sections.status_channels)}个开关量通道, "
        f"{len(sections.buses)}个母线, {len(sections.lines)}条线路, "
        f"{len(sections.transformers)}个变压器"
    )
    return sections
