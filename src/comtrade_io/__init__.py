#!/usr/bin/env python
# -*- coding: utf-8 -*-
from importlib.metadata import version

__version__ = version("comtrade_io")

from comtrade_io.comtrade import Comtrade


def version():
    return __version__
