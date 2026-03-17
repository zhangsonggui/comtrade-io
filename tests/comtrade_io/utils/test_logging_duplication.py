import logging

import comtrade_io.utils.logging as logmod


def test_logging_no_duplicate_stream_handlers():
    root = logging.getLogger()
    # 备份现有处理器
    orig_handlers = list(root.handlers)

    # 清空当前处理器，确保测试环境干净
    for h in orig_handlers:
        root.removeHandler(h)

    try:
        # 确认没有 StreamHandler
        assert sum(isinstance(h, logging.StreamHandler) for h in root.handlers) == 0

        # 第一次调用，确保至少存在一个 StreamHandler
        _ = logmod.get_logger("test_module1")
        stream_count_after_first = sum(isinstance(h, logging.StreamHandler) for h in root.handlers)
        assert stream_count_after_first >= 1

        # 第二次调用，确保数量不再增加
        _ = logmod.get_logger("test_module2")
        stream_count_after_second = sum(isinstance(h, logging.StreamHandler) for h in root.handlers)
        assert stream_count_after_second <= stream_count_after_first

    finally:
        # 还原原始状态，避免影响其他测试
        for h in list(root.handlers):
            root.removeHandler(h)
        for h in orig_handlers:
            root.addHandler(h)
