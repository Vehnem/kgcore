"""
Core API for knowledge graphs.

This package provides the main interfaces for working with knowledge graphs:
- KnowledgeGraph: High-level facade for working with KGs
- KGModel: Interface for different graph models (RDF, Property Graph, etc.)
- KGBackend: Interface for different storage backends
- KGEntity, KGRelation: Data classes for graph elements
"""

from .kg import KnowledgeGraph, KGEntity, KGRelation, KGProperty, EntityHandle, RelationHandle
from .model import KGModel
from .backend import KGBackend
from .common import KGId, Lit, Props, new_id, Result, KGError, KGNotFound, KGBackendError

__all__ = [
    # Main API
    "KnowledgeGraph",
    # Data classes
    "KGEntity",
    "KGRelation",
    "KGProperty",
    "EntityHandle",
    "RelationHandle",
    # Interfaces
    "KGModel",
    "KGBackend",
    # Common types
    "KGId",
    "Lit",
    "Props",
    "new_id",
    "Result",
    # Errors
    "KGError",
    "KGNotFound",
    "KGBackendError",
]
