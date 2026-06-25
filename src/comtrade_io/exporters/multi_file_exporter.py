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
