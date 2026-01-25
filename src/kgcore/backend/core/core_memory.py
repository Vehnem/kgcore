"""In-memory backend for simple property graph models."""

from __future__ import annotations

from typing import List, Dict
from kgcore.api.backend import KGBackend
from kgcore.api.kg import KGEntity, KGRelation, KGProperty
from kgcore.api.common.types import KGId


class InMemoryBackend(KGBackend):
    """
    Simple in-memory backend for property graph models.
    
    This is a minimal implementation for testing and simple use cases.
    For RDF models, use RDFLibBackend instead.
    """
    
    supported_model_families = ["property-graph"]
    
    def __init__(self) -> None:
        self.entities: Dict[KGId, KGEntity] = {}
        self.relations: Dict[KGId, KGRelation] = {}
    
    @property
    def name(self) -> str:
        return "in-memory"
    
    def connect(self) -> None:
        """No-op for in-memory backend."""
        pass
    
    def close(self) -> None:
        """No-op for in-memory backend."""
        pass
