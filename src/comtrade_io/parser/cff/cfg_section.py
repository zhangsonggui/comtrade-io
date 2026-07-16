from ...model.configure import Configure
from ..cfg.cfg import CfgFile
from ...utils import get_logger

logger = get_logger()


class CfgSection:
    @classmethod
    def from_str(cls, text: str) -> Configure | None:
        try:
            return CfgFile.from_str(text)
        except (ValueError, IndexError, TypeError) as e:
            logger.error(f"解析 CFF 中的 CFG 配置失败: {e}")
            return None
