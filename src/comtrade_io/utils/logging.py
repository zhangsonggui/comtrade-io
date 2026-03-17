#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import logging
from pathlib import Path
from typing import Optional

_env_files = [
    Path(__file__).resolve().parents[1] / ".env",  # comtrade/.env
    Path(__file__).resolve().parents[1] / ".." / ".env"  # repo root .env
]

_DEFAULT_LEVEL = "WARNING"
_DEFAULT_FORMAT = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
_DEFAULT_LOG_TO_FILE = False
_DEFAULT_LOG_FILE_PATH = "comtrade-io.log"


def _load_env() -> dict:
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


_env = _load_env()
_LOG_LEVEL = _env.get("LOG_LEVEL", _DEFAULT_LEVEL)
_LOG_FORMAT = _env.get("LOG_FORMAT", _DEFAULT_FORMAT)

# 文件日志配置（可选）
_LOG_TO_FILE = _env.get("LOG_TO_FILE", _DEFAULT_LOG_TO_FILE)
_LOG_FILE_PATH = _env.get("LOG_FILE_PATH",_DEFAULT_LOG_FILE_PATH)
_LOG_FILE_MAX_MB = int(_env.get("LOG_FILE_MAX_MB", "5") or 0)
_LOG_FILE_BACKUP_COUNT = int(_env.get("LOG_FILE_BACKUP_COUNT", "5") or 0)


class LineNoFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return super().format(record)


def _get_root_handler(level: int) -> logging.Handler:
    sh = logging.StreamHandler()
    sh.setLevel(level)
    fmt = LineNoFormatter(_LOG_FORMAT)
    sh.setFormatter(fmt)
    return sh


def _get_file_handler(level: int) -> Optional[logging.Handler]:
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


def _configure_root_logger():
    level = _level_from_str(_LOG_LEVEL)
    root = logging.getLogger()
    # Remove any existing StreamHandler instances to prevent duplicates
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler):
            root.removeHandler(h)
    # Always attach a single StreamHandler
    root.addHandler(_get_root_handler(level))
    root.setLevel(level)
    file_handler = _get_file_handler(level)
    if file_handler and file_handler not in root.handlers:
        root.addHandler(file_handler)


def _caller_module_name():
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
