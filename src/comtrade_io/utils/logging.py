#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""日志管理模块

基于 loguru 提供统一的日志配置和获取功能，支持环境变量配置、控制台输出和文件输出。
异常日志自动记录 traceback，并定位模块、方法、行号。
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

# 环境文件路径
_env_files = [
    Path(__file__).resolve().parents[1] / ".env",  # comtrade/.env
    Path(__file__).resolve().parents[1] / ".." / ".env"  # repo root .env
]

# 默认配置常量
_DEFAULT_LEVEL = "WARNING"
_DEFAULT_LOG_TO_FILE = False
_DEFAULT_LOG_FILE_PATH = "comtrade-io.log"
_DEFAULT_LOG_FILE_MAX_MB = "5"
_DEFAULT_LOG_FILE_BACKUP_COUNT = "5"


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


# 加载环境变量配置
_env = _load_env()
_LOG_LEVEL = _env.get("LOG_LEVEL", _DEFAULT_LEVEL)
_LOG_TO_FILE = _env.get("LOG_TO_FILE", "").lower() in ("true", "1", "yes", "on")
_LOG_FILE_PATH = _env.get("LOG_FILE_PATH", _DEFAULT_LOG_FILE_PATH)
_LOG_FILE_MAX_MB = int(_env.get("LOG_FILE_MAX_MB", _DEFAULT_LOG_FILE_MAX_MB) or 0)
_LOG_FILE_BACKUP_COUNT = int(_env.get("LOG_FILE_BACKUP_COUNT", _DEFAULT_LOG_FILE_BACKUP_COUNT) or 0)

# 全局配置标志
_configured = False


def _configure_logger():
    """配置 loguru 日志记录器

    该函数只执行一次，配置控制台处理器和可选的文件处理器。
    """
    global _configured
    if _configured:
        return

    # 移除 loguru 默认处理器
    logger.remove()

    # 日志格式：时间 | 级别 | 模块:函数:行号 - 消息
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    # 控制台输出
    logger.add(
        sys.stderr,
        level=_LOG_LEVEL,
        format=log_format,
        colorize=True,
        enqueue=True,
    )

    # 文件输出（可选）
    if _LOG_TO_FILE:
        log_path = Path(_LOG_FILE_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        rotation = f"{_LOG_FILE_MAX_MB} MB" if _LOG_FILE_MAX_MB > 0 else "5 MB"
        retention = max(0, _LOG_FILE_BACKUP_COUNT)
        logger.add(
            str(log_path),
            level=_LOG_LEVEL,
            format=log_format,
            rotation=rotation,
            retention=retention,
            enqueue=True,
            encoding="utf-8",
        )

    _configured = True


class LoguruLoggerWrapper:
    """loguru 日志包装器

    兼容标准 logging.Logger 的常用接口，支持在 except 块中自动捕获并记录异常 traceback。
    """

    def __init__(self, name: Optional[str] = None):
        self._name = name
        _configure_logger()
        self._logger = logger

    def debug(self, msg, *args, **kwargs):
        """记录 DEBUG 级别日志"""
        self._logger.opt(depth=1).debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """记录 INFO 级别日志"""
        self._logger.opt(depth=1).info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """记录 WARNING 级别日志"""
        self._logger.opt(depth=1).warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """记录 ERROR 级别日志

        如果在 except 块中调用，会自动记录异常 traceback。
        """
        if sys.exc_info()[0] is not None and not kwargs.get("exc_info"):
            self._logger.opt(depth=1, exception=True).error(msg, *args, **kwargs)
        else:
            self._logger.opt(depth=1).error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """记录 CRITICAL 级别日志

        如果在 except 块中调用，会自动记录异常 traceback。
        """
        if sys.exc_info()[0] is not None and not kwargs.get("exc_info"):
            self._logger.opt(depth=1, exception=True).critical(msg, *args, **kwargs)
        else:
            self._logger.opt(depth=1).critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """记录 ERROR 级别日志并始终附带异常 traceback"""
        self._logger.opt(depth=1, exception=True).error(msg, *args, **kwargs)


def get_logger(name: Optional[str] = None):
    """获取日志记录器

    如果未指定名称，会自动尝试获取调用者的模块名。

    参数:
        name: 日志记录器名称，可选

    返回:
        LoguruLoggerWrapper: 配置好的日志记录器包装器
    """
    if not name:
        import inspect
        try:
            stack = inspect.stack()
            for frame_info in stack[2:]:
                mod = frame_info.frame.f_globals.get("__name__")
                filename = frame_info.frame.f_globals.get("__file__")
                if filename and __file__ not in filename and mod:
                    name = mod
                    break
        except Exception:
            pass
        if not name:
            name = "comtrade.unknown"

    return LoguruLoggerWrapper(name)
