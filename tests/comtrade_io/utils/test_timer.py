"""Timer 装饰器与上下文管理器单元测试"""

import asyncio
import time

import pytest

from comtrade_io.utils.timer import Timer, timer

# ---------------- 同步函数装饰器 ----------------


def test_timer_decorator_default_name():
    """使用 @timer（不带参数）时，应正常执行并返回原函数结果"""

    @timer
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_timer_decorator_with_name():
    """使用 @timer(name=...) 显式指定名称"""

    @timer(name="my_func")
    def echo(x):
        return x

    assert echo(42) == 42


def test_timer_decorator_preserves_metadata():
    """functools.wraps 应保留原函数元信息"""

    @timer
    def my_function():
        """docstring here"""
        return None

    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "docstring here"


def test_timer_decorator_with_exception():
    """被装饰函数抛出异常时，异常应向上传播"""

    @timer
    def boom():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        boom()


# ---------------- 异步函数装饰器 ----------------


def test_timer_async_decorator():
    """异步函数应走 async_wrapper 分支并返回原结果"""

    @timer(name="async_op")
    async def async_add(a, b):
        await asyncio.sleep(0)
        return a + b

    result = asyncio.run(async_add(1, 2))
    assert result == 3


def test_timer_async_decorator_preserves_metadata():
    """异步装饰器也应保留函数元信息"""

    @timer
    async def async_func():
        """async docstring"""
        return "ok"

    assert async_func.__name__ == "async_func"
    assert async_func.__doc__ == "async docstring"


def test_timer_async_decorator_with_exception():
    """异步函数抛出异常时，异常应向上传播"""

    @timer
    async def async_boom():
        await asyncio.sleep(0)
        raise RuntimeError("async boom")

    with pytest.raises(RuntimeError, match="async boom"):
        asyncio.run(async_boom())


# ---------------- 上下文管理器 Timer ----------------


def test_timer_context_manager_basic():
    """Timer 作为上下文管理器使用，应记录耗时"""
    with Timer("block") as t:
        time.sleep(0.001)
    assert t.elapsed >= 0.0
    # elapsed 应接近 0.001，但允许误差
    assert t.elapsed < 1.0


def test_timer_context_manager_default_name():
    """未传入 name 时使用默认名"""
    with Timer() as t:
        pass
    assert t.name == "Code block"
    assert t.elapsed >= 0.0


def test_timer_context_manager_returns_self():
    """__enter__ 应返回 Timer 自身，便于访问属性"""
    with Timer("self_check") as t:
        assert isinstance(t, Timer)
        assert t.name == "self_check"


def test_timer_context_manager_propagates_exception():
    """上下文内异常应正常传播，不应被吞掉"""
    with pytest.raises(ValueError, match="ctx error"):
        with Timer("failing_block"):
            raise ValueError("ctx error")
