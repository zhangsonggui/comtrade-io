import pytest

from comtrade.utils.validators import validate_and_correct_indices


class Dummy:
    def __init__(self, index):
        self.index = index


def make_items(indices):
    return [Dummy(i) for i in indices]


def test_start_not_one_auto_correct():
    items = make_items([2, 3, 4])
    fixed, msg = validate_and_correct_indices(items, 3, "TestItem")
    assert fixed is True
    assert msg == ""
    assert [getattr(it, "index") for it in items] == [1, 2, 3]


def test_duplicates_auto_correct():
    items = make_items([1, 1, 3])
    fixed, msg = validate_and_correct_indices(items, 3, "TestItem")
    assert fixed is True
    assert msg == ""
    assert [getattr(it, "index") for it in items] == [1, 2, 3]


def test_non_contiguous_auto_correct():
    items = make_items([1, 3, 4])
    fixed, msg = validate_and_correct_indices(items, 3, "TestItem")
    assert fixed is True
    assert msg == ""
    assert [getattr(it, "index") for it in items] == [1, 2, 3]


def test_count_mismatch_raises():
    items = make_items([1, 2])
    with pytest.raises(ValueError):
        validate_and_correct_indices(items, 3, "TestItem")


def test_already_valid_no_fix():
    items = make_items([1, 2, 3])
    fixed, msg = validate_and_correct_indices(items, 3, "TestItem")
    assert fixed is False
    assert msg == ""
    assert [getattr(it, "index") for it in items] == [1, 2, 3]
