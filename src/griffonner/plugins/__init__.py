"""Plugin system for Griffonner."""

from .base import BaseBundle, BaseProcessor, SimpleProcessor
from .manager import PluginManager
from .protocols import BundleProtocol, FilterProtocol, ProcessorProtocol

__all__ = [
    "PluginManager",
    "FilterProtocol",
    "ProcessorProtocol",
    "BundleProtocol",
    "BaseProcessor",
    "BaseBundle",
    "SimpleProcessor",
]
