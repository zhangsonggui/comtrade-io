#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .base_enum import BaseEnum


class TranSide(BaseEnum):
    P = ("P", "一次侧")
    S = ("S", "二次侧")
