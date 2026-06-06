import pandas as pd

from comtrade_io.model.configure import Configure
from comtrade_io.parser.dat import DatFile
from comtrade_io.utils import get_logger

logger = get_logger()


class DatSection:
    @classmethod
    def from_str(cls, config: Configure, text: str) -> pd.DataFrame | None:
        try:
            return DatFile.from_str(config, text)
        except Exception as e:
            logger.error(f"解析 CFF 中的 DAT ASCII 数据失败: {e}")
            return None

    @classmethod
    def from_bytes(cls, config: Configure, data: bytes) -> pd.DataFrame | None:
        try:
            return DatFile.from_bytes(config, data)
        except Exception as e:
            logger.error(f"解析 CFF 中的 DAT 二进制数据失败: {e}")
            return None
