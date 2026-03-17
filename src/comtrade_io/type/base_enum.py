#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from enum import Enum
from typing import Any, cast, Dict, Optional, TypeVar

T = TypeVar('T', bound='BaseEnum')


class BaseEnum(Enum):
    """
    枚举基类：封装所有枚举通用的序列化/反序列化方法
    所有业务枚举类继承此类即可复用这些方法
    字典应遵循"key=(value,type,description)"格式
    """

    @classmethod
    def from_value(cls, value: Any, default: Optional[T] = None) -> T:
        """
        从值反序列化为枚举成员
        :param value: 枚举的值（int/str等）
        :param default: 默认值
        :return: 对应的枚举成员
        :raises ValueError: 无匹配值时抛出异常
        """
        if isinstance(value, str):
            value = value.upper()

        for member in cls:
            raw_value = member._value_
            # 支持元组格式：(value,type,description)
            if isinstance(raw_value, tuple):
                member_val = raw_value[0]
                if isinstance(member_val, str):
                    member_val = member_val.upper()
                if member_val == value:
                    return cast(T, member)
            # 支持普通格式：value
            elif raw_value == value:
                return cast(T, member)

        # 如果提供了默认值，则返回默认值
        if default is not None:
            return default

        # 构造友好的错误提示，列出所有可选值
        available_values = []
        for m in cls:
            if isinstance(m._value_, tuple):
                available_values.append(m._value_[0])
            else:
                available_values.append(m._value_)

        raise ValueError(
            f"无效的{cls.__name__}值: {value}，可选值: {available_values}"
        )

    @classmethod
    def from_name(cls, name: str) -> T:
        """
        从名称反序列化为枚举成员
        :param name: 枚举的名称（字符串，如"PENDING"）
        :return: 对应的枚举成员
        :raises ValueError: 无匹配名称时抛出异常
        """
        try:
            return cast(T, cls[name])
        except KeyError:
            available_names = [m.name for m in cls]
            raise ValueError(
                f"无效的{cls.__name__}名称: {name}，可选名称: {available_names}"
            )

    @classmethod
    def get_member_by_value(cls, value: Any) -> Optional[T]:
        """
        安全的从值获取枚举成员（无匹配时返回None，不抛异常）
        :param value: 枚举的值（支持普通值和元组值的第一个元素）
        :return: 枚举成员或None
        """
        # 将字符串值转换为大写，保持与from_value一致
        if isinstance(value, str):
            value = value.upper()

        for member in cls:
            raw_value = member._value_
            # 支持元组格式：("value", "description")
            if isinstance(raw_value, tuple):
                member_val = raw_value[0]
                if isinstance(member_val, str):
                    member_val = member_val.upper()
                if member_val == value:
                    return cast(T, member)
            # 支持普通格式：value
            elif raw_value == value:
                return cast(T, member)
        return None

    @property
    def value(self) -> Any:
        """
        获取枚举的值（如果是元组，则返回第一个元素）
        """
        if isinstance(self._value_, tuple):
            return self._value_[0]
        return self._value_

    @property
    def type(self) -> Any:
        """
        获取枚举值的类型（如果是元组，且元素数量大于2，则返回第二个元素）
        """
        if isinstance(self._value_, tuple):
            return self._value_[1] if len(self._value_) > 2 else None
        return self._value_

    @property
    def description(self) -> str:
        """
        获取枚举值的描述（如果是元组，则返回最后一个元素）
        """
        if isinstance(self._value_, tuple):
            return self._value_[-1]
        return str(self._value_)

    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典（包含名称、值、描述）
        值字段使用 get_value() 确保元组只输出第一个元素
        """
        return {
            "name" : self.name,
            "value": self.value,
            "desc" : self.description
        }

    def to_json(self, ensure_ascii: bool = False) -> str:
        """直接序列化为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii)

    @classmethod
    def list_all(cls) -> list[Dict[str, Any]]:
        """获取所有枚举成员的字典列表（用于前端下拉框等场景）"""
        return [member.to_dict() for member in cls]
