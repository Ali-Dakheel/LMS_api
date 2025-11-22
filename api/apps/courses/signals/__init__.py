"""
Courses Signals

Registers all signal handlers.
"""

from . import path_signals
from . import update_signals

__all__ = [
    'path_signals',
    'update_signals',
]