from __future__ import annotations
import importlib, pkgutil
from typing import Type
from .base import Provider
_REGISTRY: dict[str,Type[Provider]]={}
def register(name: str):
    def deco(cls: Type[Provider]): _REGISTRY[name]=cls; cls.provider_type=name; return cls
    return deco
def discover():
    import pios.providers as pkg
    for m in pkgutil.walk_packages(pkg.__path__, prefix='pios.providers.'):
        leaf=m.name.rsplit('.',1)[-1]
        if leaf not in {'base','registry','simple'}: importlib.import_module(m.name)
def create(instance):
    typ=instance['type']
    if typ not in _REGISTRY: raise KeyError(f'Unknown provider type: {typ}')
    return _REGISTRY[typ](instance)
def names(): return sorted(_REGISTRY)
