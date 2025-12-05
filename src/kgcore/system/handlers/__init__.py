"""
Handler implementations for KG tracking.

This module provides handler classes that can be used with the decorator
system. Handlers are optional - the decorator works directly with
protocol + introspection by default.
"""

from .base import KGHandler

__all__ = ["KGHandler"]

