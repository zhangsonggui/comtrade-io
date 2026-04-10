#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from pydantic import BaseModel, Field


class IndexBaseModel(BaseModel):
    """
    索引基类
    """
    index: int = Field(..., ge=0, description="索引号")


class ReferenceBaseModel(BaseModel):
    """
    参引基类
    """
    reference: Optional[str] = Field(default="", description="IEC61850参考")


class IdxOrgBaseModel(IndexBaseModel, ReferenceBaseModel):
    """
    端子排号基类
    """
    idx_org: Optional[int] = Field(default=0, ge=0, description="端子排号")
