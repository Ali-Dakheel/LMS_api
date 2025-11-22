"""
Academics Signals

Registers all signal handlers.
Import this module in apps.py ready() method.
"""

from . import term_signals
from . import enrollment_signals
from . import offering_signals

__all__ = [
    'term_signals',
    'enrollment_signals',
    'offering_signals',
]   