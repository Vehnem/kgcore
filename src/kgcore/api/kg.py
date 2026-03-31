"""
High-level model-agnostic API for knowledge graphs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Iterable
from abc import ABC, abstractmethod
from kgcore.api.common.types import KGId, new_id
from kgcore.api.model import KGModel
from kgcore.api.backend import KGBackend

@dataclass(frozen=True)
class KGProperty:
    """A property key-value pair for entities and relations."""
    key: str
    value: Any
    id: KGId = field(default_factory=new_id)
    properties: List["KGProperty"] = field(default_factory=list)
    
@dataclass(frozen=True)
class KGEntity:
    """
    Entity in the high-level KGGraph API.
    
    This is the user-facing entity representation. For the Core Graph Model
    (research/teaching IR), use `CoreNode` from `kgcore.api.cgm`.
    
    Attributes:
        id: Unique identifier
        labels: List of type/label strings
        properties: List of KGProperty instances
    """
    id: KGId = field(default_factory=new_id)
    labels: List[str] = field(default_factory=list)
    properties: List[KGProperty] = field(default_factory=list)
    
    @property
    def types(self) -> List[str]:
        """Alias for labels for compatibility."""
        return self.labels

    def get_property(self, key: str) -> List[KGProperty]:
        return [prop for prop in self.properties if prop.key == key]
    
    def get_property_value(self, key: str) -> List[KGProperty]:
        return [prop.value for prop in self.properties if prop.key == key]
    

@dataclass(frozen=True)
class KGRelation:
    """
    Relation in the high-level KGGraph API.
    
    This is the user-facing relation representation. For the Core Graph Model
    (research/teaching IR), use `CoreEdge` from `kgcore.api.cgm`.
    
    Attributes:
        type: Relation type (e.g., "KNOWS", "LOCATED_IN")
        source: Source entity ID
        target: Target entity ID
        id: Unique identifier
        properties: List of KGProperty instances
    
    Note:
        Uses `type` instead of `label` (unlike CoreEdge) for consistency
        with the high-level API naming.
    """
    type: str
    source: KGId
    target: KGId
    id: KGId = field(default_factory=new_id)
    properties: List[KGProperty] = field(default_factory=list)


# Type aliases for compatibility
EntityHandle = KGEntity
RelationHandle = KGRelation


class KnowledgeGraph:
    """
    High-level model-agnostic facade; here we only care about RDF.
    """

    def __init__(self, model: KGModel, backend: KGBackend):
        self.model = model
        self.backend = backend

        if getattr(model, "family", None) not in getattr(backend, "supported_model_families", []):
            raise ValueError(
                f"Incompatible model/backend: model family={getattr(model, 'family', None)!r} "
                f"not supported by backend {backend.name} "
                f"(supports {backend.supported_model_families})"
            )

        self.backend.connect()

    def close(self) -> None:
        self.backend.close()

    # ---- entity API ----

    def create_entity(
        self,
        id: Optional[KGId] = None,
        types: Optional[Iterable[str]] = None,
        properties: Optional[List[KGProperty]] = None,
    ) -> KGEntity:
        return self.model.create_entity(
            backend=self.backend,
            id=id,
            types=types,
            properties=properties,
        )

    def read_entity(self, id: str) -> Optional[KGEntity]:
        entity_data = self.model.get_entity(self.backend, id=id)
        if entity_data is None:
            return None
        # Convert dict to KGEntity
        properties = [KGProperty(key=k, value=v) for k, v in entity_data.get("properties", {}).items()]
        return KGEntity(
            id=entity_data["id"],
            labels=entity_data.get("types", []),
            properties=properties,
        )

    def find_entities(self, types: Optional[Iterable[str]] = None, properties: Optional[Dict[str, Any]] = None) -> List[KGEntity]:
        entities = self.model.find_entities(self.backend, types=types, properties=properties)
        return entities if isinstance(entities, list) else [entities]
        
    def update_entity(self, entity: KGEntity) -> None:
        self.model.update_entity(self.backend, entity=entity)

    def delete_entity(self, id: str) -> None:
        self.model.delete_entity(self.backend, id=id)

    # def find_entities(properties: Optional[Dict[str, Any]] = None) -> List[KGEntity]:
    #     return self.model.find_entities(self.backend, properties=properties)

    # ---- relation API ----

    def create_relation(
        self,
        source: KGId,
        target: KGId,
        type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> KGRelation:
        return self.model.create_relation(
            backend=self.backend,
            subject=source,
            predicate=type,
            object=target,
            annotations=properties,
        )

    def read_relation(self, id: str) -> Optional[KGRelation]:
        # For now, relations don't have a direct ID lookup in RDF
        # This would need to be implemented based on the model
        return None

    def update_relation(self, relation: KGRelation) -> None:
        # Update would need to delete old and create new in RDF
        raise NotImplementedError("update_relation not yet implemented")

    def get_neighbors(
        self,
        entity_id: str,
        predicate: Optional[str] = None,
    ) -> List[KGEntity]:
        """Get neighboring entities connected via relations."""
        neighbors = self.model.get_neighbors(self.backend, entity_id, predicate)
        # Convert EntityHandle to KGEntity
        return [neighbor if isinstance(neighbor, KGEntity) else KGEntity(id=neighbor.id) for neighbor in neighbors]

    def delete_relation(self, id: str) -> None:
        self.model.delete_relation(self.backend, id=id)

    # def find_relations(properties: Optional[Dict[str, Any]] = None) -> List[KGRelation]:
    #     return self.model.find_relations(self.backend, properties=properties)
