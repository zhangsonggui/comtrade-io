from comtrade_io.model.configure import Configure
from comtrade_io.parser.cfg.cfg import CfgFile
from comtrade_io.utils import get_logger

logger = get_logger()


class CfgSection:
    @classmethod
    def from_str(cls, text: str) -> Configure | None:
        try:
            return CfgFile.from_str(text)
        except Exception as e:
            logger.error(f"解析 CFF 中的 CFG 配置失败: {e}")
            return None
