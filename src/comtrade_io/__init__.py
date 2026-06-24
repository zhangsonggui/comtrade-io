from importlib.metadata import version

__version__ = version("comtrade_io")

from .model.comtrade import Comtrade

def version():
    return __version__
