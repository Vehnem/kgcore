"""
Common types and utilities for kgcore.

This module provides shared types used across the library. Note that the
Core Graph Model (CGM) in `kgcore.api.cgm` defines its own types (CoreId,
CoreLiteral, etc.) for the research/teaching IR, while this module provides
types for the high-level user-facing API.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Hashable, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    pass  # CoreLiteral would be imported from kgcore.api.cgm if it existed

# Type aliases
KGId = str

def is_uri(id: KGId) -> bool:
    # TODO improve later
    return id.startswith("http://") or id.startswith("https://")
"""
A unique identifier for graph elements in the high-level KGGraph API.

Note: The Core Graph Model (CGM) uses `CoreId = Hashable` which is more
flexible. KGId is kept as `str` for the high-level API for simplicity.
"""


@dataclass
class Lit:
    """
    Literal value for the high-level KGGraph API.
    
    This is similar to CoreLiteral in the CGM but simpler (no language tag).
    For the Core Graph Model, use `CoreLiteral` from `kgcore.api.cgm`.
    
    Attributes:
        value: The literal value as a string
        datatype: Optional datatype URI
    """
    value: str
    datatype: Optional[str] = None
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        if self.datatype:
            return f'Lit(value="{self.value}", datatype="{self.datatype}")'
        return f'Lit(value="{self.value}")'
    
    def __eq__(self, other) -> bool:
        if isinstance(other, Lit):
            return self.value == other.value and self.datatype == other.datatype
        return False


Props = Dict[str, Any | Lit]
"""
Properties dictionary for the high-level KGGraph API.

Can contain plain values or Lit instances for typed literals.
For CoreGraph, properties use `CoreLiteral` from `kgcore.api.cgm`.
"""


def new_id() -> KGId:
    """
    Generate a new unique identifier.
    
    Returns:
        A new UUID string
    """
    return str(uuid4())


@dataclass
class Result:
    """
    Lightweight return container for operations that may succeed or fail.
    
    This is a utility type used throughout the library for operations where
    exceptions might not be appropriate.

    Attributes:
        ok: True if the operation succeeded, False if it failed.
        value: The result value when ok is True; otherwise None.
        error: An error message or short description when ok is False.

    Notes:
        - Prefer returning Result over raising exceptions in low-level
          or backend code where control flow should not be interrupted.
        - Callers can check `if result.ok:` to branch on success.
    """
    ok: bool
    value: Any | None = None
    error: str | None = None


# Conversion utilities between high-level API and CGM
def lit_to_core_literal(lit: Lit) -> Any:
    """
    Convert a high-level Lit to CoreLiteral (CGM).
    
    Args:
        lit: Lit instance from high-level API
    
    Returns:
        CoreLiteral instance for CGM (if CGM module exists)
    """
    # TODO: Implement when CGM module is available
    raise NotImplementedError("CGM module not yet available")


def core_literal_to_lit(core_lit: Any) -> Lit:
    """
    Convert a CoreLiteral (CGM) to high-level Lit.
    
    Args:
        core_lit: CoreLiteral instance from CGM
    
    Returns:
        Lit instance for high-level API
    
    Note:
        Language tag is lost in conversion (Lit doesn't support it)
    """
    # TODO: Implement when CGM module is available
    raise NotImplementedError("CGM module not yet available")
