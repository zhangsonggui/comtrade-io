#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import functools
import time
from typing import Any, Callable, Optional

from .logging import get_logger

_logger = get_logger(__name__)


def timer(func: Optional[Callable[..., Any]] = None, *, name: str = "Function") -> Any:
    """
    装饰器：显示函数运行耗时
    也可以作为上下文管理器使用

    用法:
        @timer
        def my_func():
            ...

        @timer(name="my_func")
        def my_func():
            ...

        with timer("code_block"):
            # code block
    """
    if func is None:
        return lambda f: _wrap_timer(f, name)

    return _wrap_timer(func, name)


def _wrap_timer(func: Callable[..., Any], name: str) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        _logger.debug(f"{name} took {elapsed:.4f} seconds")
        return result

    @functools.wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        _logger.debug(f"{name} took {elapsed:.4f} seconds")
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return wrapper


class Timer:
    """
    上下文管理器：显示代码块运行耗时

    用法:
        with Timer("code_block"):
            # code
    """

    def __init__(self, name: str = "Code block"):
        self.name = name
        self.start: float = 0
        self.elapsed: float = 0

    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.elapsed = time.perf_counter() - self.start
        _logger.debug(f"{self.name} took {self.elapsed:.4f} seconds")
