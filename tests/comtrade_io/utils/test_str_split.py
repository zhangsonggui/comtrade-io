import pytest

from comtrade_io.utils.str_split import str_split


def test_single_line_basic():
    assert_list = str_split("a,b,c")
    assert assert_list == ["a", "b", "c"]


def test_single_line_with_spaces():
    # 注意当前实现不会对分割后的项进行 trim，因此空格会被保留在项内
    res = str_split("a, b, c")
    assert res == ["a", " b", " c"]


def test_custom_split_char():
    res = str_split("a|b|c", split_char='|')
    assert res == ["a", "b", "c"]


def test_multi_line_flatten():
    res = str_split("a,b\nc,d")
    assert res == ["a", "b", "c", "d"]


def test_crlf_handling():
    res = str_split("a,b\r\nc")
    assert res == ["a", "b", "c"]


def test_empty_and_missing_char():
    with pytest.raises(Exception):
        str_split("")
    with pytest.raises(Exception):
        str_split("abcdef")
