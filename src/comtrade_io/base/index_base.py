#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, Field


class IndexBaseModel(BaseModel):
    """索引基类

    为所有需要索引号的模型提供基础支持。

    属性:
        index: 索引号，从0开始的非负整数
    """
    index: int = Field(..., ge=0, description="索引号")


class ReferenceBaseModel(BaseModel):
    """参引基类

    为所有需要IEC61850引用的模型提供基础支持。

    属性:
        reference: IEC61850参考路径字符串
    """
    reference: Optional[str] = Field(default=None, description="IEC61850参考")


class IdxOrgBaseModel(IndexBaseModel, ReferenceBaseModel):
    """端子排号基类

    组合索引和引用功能，并增加端子排号属性。

    属性:
        index: 索引号
        reference: IEC61850参考
        idx_org: 端子排号，非负整数
    """
    idx_org: Optional[int] = Field(default=0, ge=0, description="端子排号")
