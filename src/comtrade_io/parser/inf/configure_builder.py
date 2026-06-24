from ...model.channel import Analog, Status
from ...model.configure import Configure
from ...model.description import ChannelNum, Description, Header
from .analog_section import AnalogSection
from .description_section import DescriptionSection
from .status_section import StatusSection
from .text_splitter import SectionData
from ...utils import get_logger

logger = get_logger()


def _parse_analog_params(data: dict, analog_channels: dict[int, Analog]) -> None:
    """将 ANALOG_CHANNELS_PARAMETER 节的通道参数应用到模拟通道字典

    参数段各字段含义（逗号分隔）:
        idx_cfg, idx_org, name, type(flag), freq, t1(primary), unit, t2(secondary), unit2, ad(au), bd(bu)

    参数:
        data: 参数节键值对，key 为 "CHNL_INFO_#N"，value 为逗号分隔的参数字符串
        analog_channels: 模拟通道字典（按 index 索引），会被就地更新
    """
    for key, value in data.items():
        if not key.upper().startswith("CHNL_INFO_#"):
            continue
        if not value:
            continue
        parts = [p.strip() for p in value.split(",")]
        if len(parts) < 11:
            continue

        try:
            idx_cfg = int(parts[0])
        except (ValueError, TypeError):
            continue

        param_data = {
            "index": idx_cfg,
            "idx_org": int(parts[1]) if parts[1] else 0,
            "name": parts[2],
            "type": parts[3],
            "freq": float(parts[4]) if parts[4] else 50.0,
            "t1": float(parts[5]) if parts[5] else 0.0,
            "t2": float(parts[7]) if parts[7] else 0.0,
            "ad": float(parts[9]) if parts[9] else 0.0,
            "bd": float(parts[10]) if parts[10] else 0.0,
        }

        param_obj = AnalogSection.from_dict(param_data)
        ch = analog_channels.get(idx_cfg)
        if ch is not None:
            if param_obj.primary != 1.0:
                ch.primary = param_obj.primary
            if param_obj.secondary != 1.0:
                ch.secondary = param_obj.secondary
            if param_obj.freq != 50.0:
                ch.freq = param_obj.freq
            if param_obj.au is not None:
                ch.au = param_obj.au
            if param_obj.bu is not None:
                ch.bu = param_obj.bu
            if param_obj.flag is not None:
                ch.flag = param_obj.flag
            if param_obj.type is not None:
                ch.type = param_obj.type
        else:
            analog_channels[idx_cfg] = param_obj


def _parse_status_params(data: dict, status_channels: dict[int, Status]) -> None:
    """将 STATUS_CHANNELS_PARAMETER 节的通道参数应用到开关量通道字典

    参数段各字段含义（逗号分隔）:
        idx_cfg, idx_org, name, level(type), flag_name, equipment_no

    参数:
        data: 参数节键值对
        status_channels: 开关量通道字典（按 index 索引），会被就地更新
    """
    for key, value in data.items():
        if not key.upper().startswith("CHNL_INFO_#"):
            continue
        if not value:
            continue
        parts = [p.strip() for p in value.split(",")]
        if len(parts) < 5:
            continue

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
            "obj": parts[5] if len(parts) > 5 else None,
        }

        param_obj = StatusSection.from_dict(param_data)
        ch = status_channels.get(idx_cfg)
        if ch is not None:
            if param_obj.flag is not None:
                ch.flag = param_obj.flag
            if param_obj.type is not None:
                ch.type = param_obj.type
            if param_obj.equipment_no is not None:
                ch.equipment_no = param_obj.equipment_no
        else:
            status_channels[idx_cfg] = param_obj


def build_configure(
    sections: SectionData,
    config: Configure | None = None,
) -> Configure:
    """从节数据构建或更新 Configure 对象

    若传入已有 config，则仅将参数段数据更新到 config 的通道中；
    若未传入 config，则根据节数据新建完整的 Configure（含 header 和通道）。

    参数:
        sections: 由 split_sections() 返回的节数据
        config: 可选的已有 Configure，传入时直接更新并返回

    返回:
        Configure: 构建或更新后的配置对象
    """
    if config is not None:
        logger.debug("应用参数段数据到已有Configure")
        _apply_channel_parameters(sections, config)
        return config

    logger.debug("开始构建Configure")
    return _build_from_scratch(sections)


def _build_from_scratch(sections: SectionData) -> Configure:
    """从节数据新建完整的 Configure 对象

    依次构建模拟通道、开关量通道，应用参数段数据，
    最后组装为 Configure（含文件头信息和通道数统计）。

    参数:
        sections: 节数据

    返回:
        Configure: 新建的配置对象
    """
    analog_channels: dict[int, Analog] = {}
    for ch_data in sections.analog_channels:
        ch = AnalogSection.from_dict(ch_data)
        analog_channels[ch.index] = ch

    status_channels: dict[int, Status] = {}
    for ch_data in sections.status_channels:
        ch = StatusSection.from_dict(ch_data)
        status_channels[ch.index] = ch

    _apply_channel_parameters_internal(sections, analog_channels, status_channels)

    logger.debug(
        f"构建Configure: {len(analog_channels)}个模拟通道, "
        f"{len(status_channels)}个开关量通道"
    )

    if sections.file_description:
        desc = DescriptionSection.from_dict(sections.file_description)
        return Configure(
            description=desc, analogs=analog_channels, statuses=status_channels
        )

    channel_num = ChannelNum(
        analog=len(analog_channels),
        status=len(status_channels),
        total=len(analog_channels) + len(status_channels),
    )
    return Configure(
        description=Description(header=Header(), channel_num=channel_num),
        analogs=analog_channels,
        statuses=status_channels,
    )


def _apply_channel_parameters(sections: SectionData, configure: Configure) -> None:
    """将参数段数据应用到已有 Configure 的通道中

    参数:
        sections: 节数据
        configure: 待更新的 Configure，直接修改其通道属性
    """
    if sections.analog_params_data:
        _parse_analog_params(sections.analog_params_data, configure.analogs)
    if sections.status_params_data:
        _parse_status_params(sections.status_params_data, configure.statuses)


def _apply_channel_parameters_internal(
    sections: SectionData,
    analog_channels: dict[int, Analog],
    status_channels: dict[int, Status],
) -> None:
    """将参数段数据更新到通道字典中（内部使用，新建场景）

    与 _apply_channel_parameters 的区别在于此函数直接操作 dict 而非 Configure 对象。

    参数:
        sections: 节数据
        analog_channels: 模拟通道字典（就地修改）
        status_channels: 开关量通道字典（就地修改）
    """
    if sections.analog_params_data:
        _parse_analog_params(sections.analog_params_data, analog_channels)
    if sections.status_params_data:
        _parse_status_params(sections.status_params_data, status_channels)
