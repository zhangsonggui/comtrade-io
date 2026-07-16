"""Comtrade.get_changed_statuses 数字量变位记录单元测试"""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from comtrade_io.model.channel import Status
from comtrade_io.model.comtrade import Comtrade
from comtrade_io.model.configure import Configure
from comtrade_io.model.description import ChannelNum, Description
from comtrade_io.model.type import Phase


def _make_comtrade(
    data: pd.DataFrame | None,
    analog_count: int = 1,
    status_defs: dict[int, Status] | None = None,
    start_time: datetime | None = datetime(2024, 1, 1),
) -> Comtrade:
    """构造测试用 Comtrade 对象

    默认 1 个模拟量 + 给定数字量；data 的列布局需与 analog_count/status 匹配。
    """
    config = Configure()
    config.description = Description()
    status_count = len(status_defs or {})
    config.description.channel_num = ChannelNum(
        total=analog_count + status_count,
        analog=analog_count,
        status=status_count,
    )
    config.description.file_start_time = start_time
    if status_defs:
        for idx, st in status_defs.items():
            config.statuses[idx] = st
    return Comtrade(config=config, data=data)


def _status(index: int, name: str = "D") -> Status:
    return Status(index=index, name=f"{name}{index}", phase=Phase.NONE)


class TestGetChangedStatuses:
    """核心变位检测逻辑"""

    def test_detects_two_transitions(self):
        """status1: 0->0->1->1->0，应记录 2 次变位 + 1 个初始状态"""
        data = pd.DataFrame(
            {
                0: [1, 2, 3, 4, 5],
                1: [0, 1000, 2000, 3000, 4000],
                2: [1.0, 2.0, 3.0, 4.0, 5.0],
                3: [0, 0, 1, 1, 0],
                4: [1, 1, 1, 1, 1],
            }
        )
        ct = _make_comtrade(
            data,
            analog_count=1,
            status_defs={1: _status(1), 2: _status(2)},
        )
        changed = ct.get_changed_statuses()
        assert len(changed) == 1
        st = changed[0]
        assert st.index == 1
        records = st.change_records
        assert records is not None and len(records) == 3

        # 初始记录：采样点 1，状态 0
        assert records[0].sample_point == 1
        assert records[0].state == 0
        assert records[0].timestamp == datetime(2024, 1, 1)

        # 第一次变位：采样点 3，状态 1
        assert records[1].sample_point == 3
        assert records[1].state == 1
        assert records[1].timestamp == datetime(2024, 1, 1) + timedelta(
            microseconds=2000
        )

        # 第二次变位：采样点 5，状态 0
        assert records[2].sample_point == 5
        assert records[2].state == 0
        assert records[2].timestamp == datetime(2024, 1, 1) + timedelta(
            microseconds=4000
        )

    def test_unchanged_status_excluded(self):
        """全程无变位的通道不应出现在结果中"""
        data = pd.DataFrame(
            {
                0: [1, 2, 3],
                1: [0, 1000, 2000],
                2: [1.0, 2.0, 3.0],
                3: [1, 1, 1],
            }
        )
        ct = _make_comtrade(data, analog_count=1, status_defs={1: _status(1)})
        assert ct.get_changed_statuses() == []

    def test_single_sample_returns_empty(self):
        """只有 1 个采样点时，只有初始记录，len(records) <= 1，不加入结果"""
        data = pd.DataFrame(
            {
                0: [1],
                1: [0],
                2: [1.0],
                3: [1],
            }
        )
        ct = _make_comtrade(data, analog_count=1, status_defs={1: _status(1)})
        assert ct.get_changed_statuses() == []

    def test_first_sample_initial_state_recorded(self):
        """初始状态无论 0 或 1，都应作为首条记录"""
        data = pd.DataFrame(
            {
                0: [1, 2],
                1: [0, 1000],
                2: [1.0, 2.0],
                3: [1, 0],  # 初始 1，第2点变 0
            }
        )
        ct = _make_comtrade(data, analog_count=1, status_defs={1: _status(1)})
        changed = ct.get_changed_statuses()
        assert len(changed) == 1
        records = changed[0].change_records
        assert records is not None
        assert records[0].sample_point == 1
        assert records[0].state == 1
        assert records[1].sample_point == 2
        assert records[1].state == 0


class TestGetChangedStatusesEdgeCases:
    """边界条件"""

    def test_data_none_returns_empty(self):
        ct = _make_comtrade(None, analog_count=1, status_defs={1: _status(1)})
        assert ct.get_changed_statuses() == []

    def test_empty_dataframe_returns_empty(self):
        data = pd.DataFrame()
        ct = _make_comtrade(data, analog_count=1, status_defs={1: _status(1)})
        assert ct.get_changed_statuses() == []

    def test_no_statuses_returns_empty(self):
        data = pd.DataFrame(
            {
                0: [1, 2],
                1: [0, 1000],
                2: [1.0, 2.0],
            }
        )
        ct = _make_comtrade(data, analog_count=1, status_defs={})
        assert ct.get_changed_statuses() == []

    def test_col_index_out_of_range_skipped(self):
        """status.index 超出数据列数时，该通道应被跳过而不抛异常"""
        data = pd.DataFrame(
            {
                0: [1, 2],
                1: [0, 1000],
                2: [1.0, 2.0],
                # 仅 1 个 status 列（col 3），但定义了 status 1 和 2
            }
        )
        ct = _make_comtrade(
            data, analog_count=1, status_defs={1: _status(1), 2: _status(2)}
        )
        # status1 列存在 -> 有变位时返回；status2 列不存在 -> 跳过
        # 但 status1 数据 [1,1] 无变位，所以整体返回空
        assert ct.get_changed_statuses() == []

    def test_start_time_none_timestamp_none(self):
        """start_time 为 None 时，变位记录的 timestamp 应为 None"""
        data = pd.DataFrame(
            {
                0: [1, 2],
                1: [0, 1000],
                2: [1.0, 2.0],
                3: [0, 1],
            }
        )
        ct = _make_comtrade(
            data,
            analog_count=1,
            status_defs={1: _status(1)},
            start_time=None,
        )
        changed = ct.get_changed_statuses()
        assert len(changed) == 1
        for record in changed[0].change_records:
            assert record.timestamp is None

    def test_multiple_channels_with_changes(self):
        """多个通道同时存在变位时都应返回"""
        data = pd.DataFrame(
            {
                0: [1, 2, 3],
                1: [0, 1000, 2000],
                2: [1.0, 2.0, 3.0],
                3: [0, 1, 1],  # status1 变位
                4: [1, 1, 0],  # status2 变位
            }
        )
        ct = _make_comtrade(
            data,
            analog_count=1,
            status_defs={1: _status(1), 2: _status(2)},
        )
        changed = ct.get_changed_statuses()
        assert len(changed) == 2
        changed_indices = {s.index for s in changed}
        assert changed_indices == {1, 2}
