from ..inf import InfFile
from ...utils import get_logger

logger = get_logger()


class InfSection:
    @classmethod
    def from_str(cls, text: str):
        try:
            return InfFile.from_str(text).to_equipment_group()
        except Exception as e:
            logger.error(f"解析 CFF 中的 INF 信息失败: {e}")
            return None
