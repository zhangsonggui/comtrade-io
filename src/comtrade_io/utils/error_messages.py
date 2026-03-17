#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""错误消息常量模块"""


class ErrorMessage:
    """统一的错误消息模板"""

    # 文件相关错误
    FILE_NOT_FOUND = "文件不存在: {}"
    FILE_NOT_A_FILE = "路径不是一个文件: {}"
    FILE_SIZE_EXCEEDS_LIMIT = "文件大小超出限制: {:.2f}MB > {}MB"
    INVALID_FILE_SUFFIX = "文件后缀名错误，期望: {}, 实际: {}"
    FILE_READ_ERROR = "读取文件失败: {}"
    FILE_WRITE_ERROR = "写入文件失败: {}"

    # 索引相关错误
    INDEX_OUT_OF_RANGE = "索引值应在[1, {}]之间，输入的: {}超出范围"
    INDEX_NOT_START_FROM_ONE = "索引未从1开始，第一个索引: {}"
    DUPLICATE_INDEX_FOUND = "{}存在重复索引"
    INDEX_NOT_CONTINUOUS = "{}索引不连续，缺失: {}, 多余: {}"

    # 配置相关错误
    CONFIG_CHANNEL_COUNT_MISMATCH = "{}数量不匹配，期望{}个，实际{}个"
    CONFIG_FILE_LINE_COUNT_ERROR = "配置文件{}行数不对应, {}"
    CONFIG_FILE_PARSE_ERROR = "解析配置文件失败: {}"

    # 数据相关错误
    DATA_SAMPLE_COUNT_MISMATCH = "数据文件{}中实际采样点{}与配置文件定义采样点{}不一致"
    DATA_COLUMN_COUNT_MISMATCH = "数据文件{}中实际列数{}与期望列数{}不一致"
    DATA_SPLIT_ERROR = "数据文件{}数据拆分错误，期望读取{}列，实际读取{}列"

    # 通道相关错误
    CHANNEL_NOT_FOUND = "通道不存在，索引: {}"
    CHANNEL_TYPE_MISMATCH = "通道类型不匹配，期望: {}, 实际: {}"

    # 枚举相关错误
    INVALID_ENUM_VALUE = "无效的{}值: {}, 可选值: {}"
    INVALID_ENUM_NAME = "无效的{}名称: {}, 可选名称: {}"

    # 其他错误
    INVALID_PARAMETER = "传入的参数错误: {}"
    NOT_IMPLEMENTED = "功能未实现: {}"
    INVALID_OPERATION = "无效的操作: {}"
