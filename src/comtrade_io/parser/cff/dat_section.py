import pandas as pd

from ...model.configure import Configure
from ..dat import DatFile
from ...utils import get_logger

logger = get_logger()


class DatSection:
    @classmethod
    def from_str(cls, config: Configure, text: str) -> pd.DataFrame | None:
        try:
            text = cls._sanitize_text(text)
            return DatFile.from_str(config, text)
        except Exception as e:
            logger.error(f"解析 CFF 中的 DAT ASCII 数据失败: {e}")
            return None

    @staticmethod
    def _sanitize_text(text: str) -> str:
        """移除控制字符（保留 \\n、\\r、\\t）"""
        return "".join(c for c in text if c == "\n" or c == "\r" or c == "\t" or c >= " ")

    @classmethod
    def from_bytes(cls, config: Configure, data: bytes) -> pd.DataFrame | None:
        try:
            return DatFile.from_bytes(config, data)
        except Exception as e:
            logger.error(f"解析 CFF 中的 DAT 二进制数据失败: {e}")
            return None
