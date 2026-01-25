"""
Common types and utilities for kgcore.

This module provides shared types used across the library for the high-level
KGGraph API. For Core Graph Model types, see `kgcore.api.cgm`.
"""

from .types import (
    KGId,
    Lit,
    Props,
    new_id,
    Result,
    lit_to_core_literal,
    core_literal_to_lit,
)

from .errors import (
    KGError,
    KGNotFound,
    KGBackendError,
)

__all__ = [
    # Types
    "KGId",
    "Lit",
    "Props",
    "new_id",
    "Result",
    # Converters
    "lit_to_core_literal",
    "core_literal_to_lit",
    # Errors
    "KGError",
    "KGNotFound",
    "KGBackendError",
]

