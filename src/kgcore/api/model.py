from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, List, Optional, TYPE_CHECKING

from kgcore.api.backend import KGBackend
from kgcore.api.common.types import KGId

if TYPE_CHECKING:
    from kgcore.api.kg import KGEntity, KGRelation, EntityHandle, RelationHandle

class KGModel(ABC):
    """
    Knows how high-level KG ops map to this model (RDF, PG, ...).
    """

    # e.g. "rdf", "property-graph"
    family: str

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    # ---- entity operations ----

    @abstractmethod
    def create_entity(
        self,
        backend: KGBackend,
        id: Optional[str] = None,
        types: Optional[Iterable[str]] = None,
        properties: Optional[List[Any] | Dict[str, Any]] = None,
    ) -> "KGEntity":
        ...

    @abstractmethod
    def get_entity(
        self,
        backend: KGBackend,
        id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get entity data as a dictionary with 'id', 'types', and 'properties' keys."""
        ...

    @abstractmethod
    def find_entities(
        self,
        backend: KGBackend,
        types: Optional[Iterable[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> List[KGEntity]:
        ...

    @abstractmethod
    def delete_entity(
        self,
        backend: KGBackend,
        id: str,
    ) -> None:
        ...

    @abstractmethod
    def update_entity(
        self,
        backend: KGBackend,
        entity: "KGEntity",
    ) -> None:
        """Update an existing entity."""
        ...

    # ---- relation operations ----

    @abstractmethod
    def create_relation(
        self,
        backend: KGBackend,
        subject: str,
        predicate: str,
        object: str,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> "KGRelation":
        ...

    @abstractmethod
    def get_neighbors(
        self,
        backend: KGBackend,
        entity_id: str,
        predicate: Optional[str] = None,
    ) -> List["KGEntity"]:
        """Get neighboring entities connected via relations."""
        ...

    # Generic annotation hooks
    def annotate(
        self,
        backend: KGBackend,
        target: KGId,
        annotations: dict[str, Any],
    ) -> None:
        raise NotImplementedError("Annotations not supported by this model")

    def get_annotations(
        self,
        backend: KGBackend,
        target: KGId,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError("Annotations not supported by this model")

    def get_relation(
        self,
        backend: KGBackend,
        id: str,
    ) -> Optional["KGRelation"]:
        """Get a relation by ID. Not all models support this."""
        raise NotImplementedError("get_relation not supported by this model")

    def update_relation(
        self,
        backend: KGBackend,
        relation: "KGRelation",
    ) -> None:
        """Update an existing relation."""
        raise NotImplementedError("update_relation not supported by this model")

    def delete_relation(
        self,
        backend: KGBackend,
        id: str,
    ) -> None:
        """Delete a relation by ID."""
        raise NotImplementedError("delete_relation not supported by this model")




