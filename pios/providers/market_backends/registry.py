from __future__ import annotations
import importlib,pkgutil
from typing import Type
from .base import MarketBackend
_BACKENDS:dict[str,Type[MarketBackend]]={}
def register_backend(name:str):
    def deco(cls:Type[MarketBackend]):_BACKENDS[name]=cls;cls.name=name;return cls
    return deco
def discover_backends():
    import pios.providers.market_backends as pkg
    for m in pkgutil.iter_modules(pkg.__path__):
        if m.name not in {'base','registry'}:importlib.import_module(f'pios.providers.market_backends.{m.name}')
def get_backend(name:str)->MarketBackend:return _BACKENDS[name]()
def backend_names():return sorted(_BACKENDS)
