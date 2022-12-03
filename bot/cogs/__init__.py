"""Cogs module, set enabled cogs here for automatic import"""
from .generic import Generic, GenericSlash
from .lodestone import Lodestone
from .events import Events


# Register Cogs that should be enabled:
enabled_cogs = [Generic, Lodestone, Events, GenericSlash]
