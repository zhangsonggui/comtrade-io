"""
DMF设备部件基类模块

定义DMF设备部件的基类，提供从XML元素解析设备通用属性的功能。
"""
from typing import List, Set
from xml.etree.ElementTree import Element

from ...model.channel.analog import Analog
from ...model.channel.status import Status
from ...model.equipment.equipment import Equipment
from ...utils import parse_int


def _find_all_elements(element: Element, ns: dict, tag_name: str) -> List[Element]:
    elems = []
    if 'scl' in ns:
        elems = element.findall(f'scl:{tag_name}', ns)
    if not elems and 'ns' in ns:
        elems = element.findall(f'ns:{tag_name}', ns)
    if not elems:
        elems = element.findall(tag_name)
    if not elems:
        for prefix, uri in ns.items():
            if uri:
                elems = element.findall(f'{{{uri}}}{tag_name}')
                if elems:
                    break
    return elems


def _extract_indices(
    element: Element, ns: dict, tag_attrs: list[tuple[str, list[str]]]
) -> Set[int]:
    """从XML元素中提取通道索引

    参数:
        element: XML元素
        ns: 命名空间映射
        tag_attrs: 列表，每个元素为 (标签名, 属性名列表)

    返回:
        通道索引集合
    """
    indices = set()

    for tag_name, attrs in tag_attrs:
        elems = _find_all_elements(element, ns, tag_name)
        for chn in elems:
            for attr in attrs:
                val = chn.get(attr)
                if val:
                    idx = parse_int(val)
                    if idx > 0:
                        indices.add(idx)

    for child in element:
        child_indices = _extract_indices(child, ns, tag_attrs)
        indices.update(child_indices)

    return indices


ANALOG_TAG_ATTRS = [
    ("AnaChn", ["idx_cfg"]),
    ("ACVChn", ["ua_idx", "ub_idx", "uc_idx", "un_idx", "ul_idx"]),
    ("ACC_Bran", ["ia_idx", "ib_idx", "ic_idx", "in_idx"]),
    ("ACI_Bran", ["ia_idx", "ib_idx", "ic_idx", "in_idx"]),
    ("SDL_RelatedAnalog", ["a1", "a2", "a3", "a4"]),
]

STATUS_TAG_ATTRS = [
    ("StaChn", ["idx_cfg"]),
    (
        "SDL_Breaker",
        [
            "breaker_a",
            "breaker_b",
            "breaker_c",
            "breaker_a2",
            "breaker_b2",
            "breaker_c2",
        ],
    ),
    ("SDL_OtherDigital", ["d1", "d2", "d3", "d4"]),
]


def _extract_analog_indices(element: Element, ns: dict) -> Set[int]:
    return _extract_indices(element, ns, ANALOG_TAG_ATTRS)


def _extract_status_indices(element: Element, ns: dict) -> Set[int]:
    indices = _extract_indices(element, ns, STATUS_TAG_ATTRS)

    protect_elems = _find_all_elements(element, ns, 'SDL_Protect')
    for chn in protect_elems:
        for attr in chn.keys():
            if attr.startswith(('a_trip', 'b_trip', 'c_trip', 'reclose')):
                val = chn.get(attr)
                if val:
                    idx = parse_int(val)
                    if idx > 0:
                        indices.add(idx)
    return indices


def _parse_channels_from_xml(
    element: Element,
    ns: dict,
    channels_dict: dict | None,
    extract_fn,
    use_scl_prefix: bool = True,
) -> list:
    if not channels_dict:
        return []

    indices = extract_fn(element, ns)
    result = []
    for idx in sorted(indices):
        if idx in channels_dict:
            result.append(channels_dict[idx])
    return result


def parse_ans_from_xml(
    element: Element,
    ns: dict,
    analog_channels: dict = None,
    use_scl_prefix: bool = True,
) -> List[Analog]:
    return _parse_channels_from_xml(
        element, ns, analog_channels, _extract_analog_indices
    )


def parse_sts_from_xml(element: Element, ns: dict, status_channels: dict = None,
                       use_scl_prefix: bool = True) -> List[Status]:
    return _parse_channels_from_xml(
        element, ns, status_channels, _extract_status_indices
    )


class EquipmentElement:
    """DMF设备部件基类"""

    @classmethod
    def from_xml(cls,
                 element: Element,
                 ns: dict,
                 analog_channels: dict = None,
                 status_channels: dict = None) -> Equipment:
        index = parse_int(element.get('idx', 1))
        name = element.get('bus_name', element.get('line_name', element.get('trm_name', '')))
        reference = element.get('srcRef', '')
        uuid = element.get('bus_uuid', element.get('line_uuid', element.get('transformer_uuid', '')))

        anas = parse_ans_from_xml(element, ns, analog_channels)
        stas = parse_sts_from_xml(element, ns, status_channels)

        return Equipment(
                index=index,
                name=name,
                reference=reference,
                uuid=uuid,
                anas=anas,
                stas=stas
        )
