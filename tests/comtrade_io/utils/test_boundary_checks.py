#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""边界检查工具测试"""
import pytest

from comtrade_io.verify.boundary_checks import (check_index_range, check_not_empty, check_positive, clamp)


class TestBoundaryChecks:
    """边界检查工具测试类"""

    def test_check_index_range_valid(self):
        """测试有效的索引范围"""
        assert check_index_range(5, 1, 10) == True
        assert check_index_range(1, 1, 10) == True
        assert check_index_range(10, 1, 10) == True

    def test_check_index_range_invalid(self):
        """测试无效的索引范围"""
        with pytest.raises(IndexError):
            check_index_range(0, 1, 10)
        with pytest.raises(IndexError):
            check_index_range(11, 1, 10)
        with pytest.raises(IndexError):
            check_index_range(-5, 1, 10)

    def test_check_index_range_no_raise(self):
        """测试不抛出异常的索引检查"""
        assert check_index_range(0, 1, 10, raise_error=False) == False
        assert check_index_range(11, 1, 10, raise_error=False) == False
        assert check_index_range(5, 1, 10, raise_error=False) == True

    def test_check_positive(self):
        """测试正数检查"""
        assert check_positive(5) == True
        assert check_positive(0.1) == True
        assert check_positive(0, allow_zero=True) == True
        assert check_positive(-1) == False
        assert check_positive(0) == False

    def test_check_not_empty(self):
        """测试非空字符串检查"""
        assert check_not_empty("test") == True
        assert check_not_empty("  test  ") == True

        with pytest.raises(ValueError):
            check_not_empty("")
        with pytest.raises(ValueError):
            check_not_empty("   ")
        with pytest.raises(ValueError):
            check_not_empty(None)

    def test_clamp(self):
        """测试值限制"""
        assert clamp(5, 1, 10) == 5
        assert clamp(0, 1, 10) == 1
        assert clamp(15, 1, 10) == 10
        assert clamp(-5, 1, 10) == 1
        assert clamp(7.5, 1, 10) == 7.5
        assert clamp(0.5, 1, 10) == 1

    def test_clamp_with_floats(self):
        """测试浮点数限制"""
        assert clamp(3.14, 0.0, 5.0) == 3.14
        assert clamp(-1.5, 0.0, 5.0) == 0.0
        assert clamp(10.0, 0.0, 5.0) == 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
