#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""日志管理模块

提供统一的日志配置和获取功能，支持环境变量配置、控制台输出和文件输出。
"""

import inspect
import logging
from pathlib import Path
from typing import Optional

# 环境文件路径
_env_files = [
    Path(__file__).resolve().parents[1] / ".env",  # comtrade/.env
    Path(__file__).resolve().parents[1] / ".." / ".env"  # repo root .env
]

# 默认配置常量
_DEFAULT_LEVEL = "WARNING"
_DEFAULT_FORMAT = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
_DEFAULT_LOG_TO_FILE = False
_DEFAULT_LOG_FILE_PATH = "comtrade-io.log"


def _load_env() -> dict:
    """从.env文件加载环境变量配置

    按优先级查找.env文件，加载键值对配置。

    返回:
        dict: 加载的环境变量字典
    """
    env = {}
    for env_path in _env_files:
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            k, v = line.split("=", 1)
                            env[k.strip()] = v.strip().strip('"').strip("'")
            except Exception:
                pass
            break
    return env


def _level_from_str(level_str: str) -> int:
    """将日志级别字符串转换为logging模块的级别常量

    参数:
        level_str: 日志级别字符串，如"DEBUG"、"INFO"、"WARNING"等

    返回:
        int: 对应的logging级别常量
    """
    level = level_str.upper()
    mapping = {
        "CRITICAL": logging.CRITICAL,
        "ERROR"   : logging.ERROR,
        "WARNING" : logging.WARNING,
        "WARN"    : logging.WARNING,
        "INFO"    : logging.INFO,
        "DEBUG"   : logging.DEBUG,
        "NOTSET"  : logging.NOTSET,
    }
    return mapping.get(level, logging.INFO)


# 加载环境变量配置
_env = _load_env()
_LOG_LEVEL = _env.get("LOG_LEVEL", _DEFAULT_LEVEL)
_LOG_FORMAT = _env.get("LOG_FORMAT", _DEFAULT_FORMAT)

# 文件日志配置（可选）
_log_to_file_str = _env.get("LOG_TO_FILE", "")
_LOG_TO_FILE = _log_to_file_str.lower() in ("true", "1", "yes", "on") if _log_to_file_str else _DEFAULT_LOG_TO_FILE
_LOG_FILE_PATH = _env.get("LOG_FILE_PATH",_DEFAULT_LOG_FILE_PATH)
_LOG_FILE_MAX_MB = int(_env.get("LOG_FILE_MAX_MB", "5") or 0)
_LOG_FILE_BACKUP_COUNT = int(_env.get("LOG_FILE_BACKUP_COUNT", "5") or 0)


class LineNoFormatter(logging.Formatter):
    """日志格式化器

    继承自logging.Formatter，提供带行号的日志格式化功能。
    """

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录

        参数:
            record: 日志记录对象

        返回:
            str: 格式化后的日志字符串
        """
        return super().format(record)


def _get_root_handler(level: int) -> logging.Handler:
    """获取控制台日志处理器

    参数:
        level: 日志级别

    返回:
        logging.Handler: 配置好的控制台日志处理器
    """
    sh = logging.StreamHandler()
    sh.setLevel(level)
    fmt = LineNoFormatter(_LOG_FORMAT)
    sh.setFormatter(fmt)
    return sh


def _get_file_handler(level: int) -> Optional[logging.Handler]:
    """获取文件日志处理器

    参数:
        level: 日志级别

    返回:
        Optional[logging.Handler]: 配置好的文件日志处理器，如果未启用文件日志则返回None
    """
    if not _LOG_TO_FILE:
        return None
    log_path = Path(_LOG_FILE_PATH) if _LOG_FILE_PATH else (
                Path(__file__).resolve().parents[2] / "logs" / "comtrade.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if _LOG_FILE_MAX_MB and _LOG_FILE_MAX_MB > 0:
        from logging.handlers import RotatingFileHandler
        handler = RotatingFileHandler(str(log_path), maxBytes=_LOG_FILE_MAX_MB * 1024 * 1024,
                                      backupCount=max(0, _LOG_FILE_BACKUP_COUNT))
    else:
        from logging import FileHandler
        handler = FileHandler(str(log_path))
    handler.setLevel(level)
    handler.setFormatter(LineNoFormatter(_LOG_FORMAT))
    return handler


# 全局配置标志
_configured = False


def _configure_root_logger():
    """配置根日志记录器

    该函数只执行一次，配置控制台处理器和可选的文件处理器。
    """
    global _configured
    if _configured:
        return

    level = _level_from_str(_LOG_LEVEL)
    root = logging.getLogger()
    # Remove any existing handlers to prevent duplicates
    for h in list(root.handlers):
        root.removeHandler(h)
    # Always attach a single StreamHandler
    root.addHandler(_get_root_handler(level))
    root.setLevel(level)
    file_handler = _get_file_handler(level)
    if file_handler:
        root.addHandler(file_handler)
    _configured = True


def _caller_module_name():
    """获取调用者模块名

    通过检查调用栈，动态获取调用 get_logger 的模块名称。

    返回:
        Optional[str]: 调用者模块名，无法确定时返回None
    """
    # 尝试动态获取调用者模块名
    frame = None
    try:
        stack = inspect.stack()
        # 从第三帧开始往上找，避免获取 logging 自身的帧
        for frame_info in stack[2:]:
            mod = frame_info.frame.f_globals.get("__name__")
            filename = frame_info.frame.f_globals.get("__file__")
            if filename and __file__ not in filename and mod:
                return mod
        return None
    finally:
        if frame is not None:
            del frame


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志记录器

    如果未指定名称，会自动尝试获取调用者的模块名。

    参数:
        name: 日志记录器名称，可选

    返回:
        logging.Logger: 配置好的日志记录器
    """
    _configure_root_logger()

    if not name:
        derived = _caller_module_name()
        name = derived if derived else "comtrade.unknown"

    logger = logging.getLogger(name)

    if not logger.handlers:
        # Do not attach root handlers to child loggers to avoid duplicate outputs.
        # Rely on root logger configuration and propagation.
        pass

    return logger
