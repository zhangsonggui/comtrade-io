from comtrade_io.utils.text_utils import text_split


def test_single_line_basic():
    assert_list = text_split("a,b,c")
    assert assert_list == ["a", "b", "c"]


def test_single_line_with_spaces():
    # text_split 默认会去除首尾空白
    res = text_split("a, b, c")
    assert res == ["a", "b", "c"]


def test_custom_split_char():
    res = text_split("a|b|c", split_char="|")
    assert res == ["a", "b", "c"]


def test_multi_line_flatten():
    res = text_split("a,b\nc,d")
    assert res == ["a", "b", "c", "d"]


def test_crlf_handling():
    res = text_split("a,b\r\nc")
    assert res == ["a", "b", "c"]


def test_empty_and_missing_char():
    # text_split 对空字符串返回空列表，不抛异常
    res = text_split("")
    assert res == []
    res = text_split("abcdef")
    assert res == ["abcdef"]
