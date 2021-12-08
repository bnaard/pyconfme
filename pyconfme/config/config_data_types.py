"""Provides an enum-like class defining known config-file types"""

from enum import Enum, auto

class ConfigDataTypes(Enum):
    """Provides an enum-like class defining known config-file types"""
    toml = auto()
    json = auto()
    yaml = auto()
    infer = auto()
    unknown = auto()
