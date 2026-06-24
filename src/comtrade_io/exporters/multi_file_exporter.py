from pathlib import Path
from typing import TYPE_CHECKING

from ..parser.comtrade_file import ComtradeFile
from ..parser.dat import DatFile
from ..utils import get_logger

if TYPE_CHECKING:
    from ..model.comtrade import Comtrade

logger = get_logger()


def export_multi_file(
    comtrade: "Comtrade",
    output_path: "str | Path | ComtradeFile",
    data_format: str,
    **kwargs,
) -> bool:
    cf = ComtradeFile.from_path(output_path)

    # ASCII 导出时：时间戳转换为纳秒整型，超量程则调整时标倍率因子
    if data_format == "ASCII" and comtrade.data is not None:
        _prepare_ascii_timestamps(comtrade)

    comtrade.write_cfg(str(cf.cfg_path.path))
    DatFile(comtrade.config).write(
        cf.dat_path.path, comtrade.data, data_type=data_format
    )
    if cf.inf_path.path:
        try:
            comtrade.write_inf(str(cf.inf_path.path))
        except Exception as e:
            logger.warning(f"INF 文件导出失败（不影响整体导出）: {e}")
    if cf.dmf_path.path:
        try:
            comtrade.write_dmf(str(cf.dmf_path.path))
        except Exception as e:
            logger.warning(f"DMF 文件导出失败（不影响整体导出）: {e}")
    logger.info(f"多文件导出成功: {cf.cfg_path.path}")
    return True


def _prepare_ascii_timestamps(comtrade: "Comtrade") -> None:
    """将数据时间戳转换为纳秒整型，超 int32 量程时调整 timemult"""
    import numpy as np

    ts = comtrade.data.iloc[:, 1]
    ts_ns = np.round(ts * 1000).astype(np.int64)
    max_ts = ts_ns.max()

    divisor = 1
    INT32_MAX = 2_147_483_647
    if max_ts > INT32_MAX:
        divisor = int(np.ceil(max_ts / INT32_MAX))

    comtrade.data.iloc[:, 1] = (ts_ns / divisor).astype(np.int64)
    comtrade.config.description.timemult = divisor * 0.001
