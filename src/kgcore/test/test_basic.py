"""Basic tests for kgcore API."""

import pytest
from kgcore.api import KnowledgeGraph, KGEntity, KGRelation, KGProperty
from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel


def test_create_entity():
    """Test creating an entity."""
    backend = RDFLibBackend()
    model = RDFBaseModel()
    kg = KnowledgeGraph(model=model, backend=backend)
    
    alice_iri = "http://example.org/Alice"
    person_iri = "http://example.org/Person"
    name_prop_iri = "http://example.org/name"
    
    entity = kg.create_entity(
        id=alice_iri,
        types=[person_iri],
        properties=[KGProperty(key=name_prop_iri, value="Alice")],
    )
    
    assert entity.id == alice_iri
    assert person_iri in entity.labels
    assert len(entity.properties) == 1
    assert entity.properties[0].key == name_prop_iri
    assert entity.properties[0].value == "Alice"
    
    kg.close()


def test_read_entity():
    """Test reading an entity."""
    backend = RDFLibBackend()
    model = RDFBaseModel()
    kg = KnowledgeGraph(model=model, backend=backend)
    
    alice_iri = "http://example.org/Alice"
    person_iri = "http://example.org/Person"
    name_prop_iri = "http://example.org/name"
    
    # Create entity
    kg.create_entity(
        id=alice_iri,
        types=[person_iri],
        properties=[KGProperty(key=name_prop_iri, value="Alice")],
    )
    
    # Read it back
    entity = kg.read_entity(alice_iri)
    assert entity is not None
    assert entity.id == alice_iri
    assert person_iri in entity.labels
    
    kg.close()


def test_create_relation():
    """Test creating a relation."""
    backend = RDFLibBackend()
    model = RDFBaseModel()
    kg = KnowledgeGraph(model=model, backend=backend)
    
    alice_iri = "http://example.org/Alice"
    bob_iri = "http://example.org/Bob"
    knows_iri = "http://example.org/knows"
    
    # Create entities first
    kg.create_entity(id=alice_iri, types=[])
    kg.create_entity(id=bob_iri, types=[])
    
    # Create relation
    relation = kg.create_relation(
        source=alice_iri,
        target=bob_iri,
        type=knows_iri,
    )
    
    assert relation.source == alice_iri
    assert relation.target == bob_iri
    assert relation.type == knows_iri
    
    kg.close()


def test_get_neighbors():
    """Test getting neighbors."""
    backend = RDFLibBackend()
    model = RDFBaseModel()
    kg = KnowledgeGraph(model=model, backend=backend)
    
    alice_iri = "http://example.org/Alice"
    bob_iri = "http://example.org/Bob"
    charlie_iri = "http://example.org/Charlie"
    knows_iri = "http://example.org/knows"
    
    # Create entities
    kg.create_entity(id=alice_iri, types=[])
    kg.create_entity(id=bob_iri, types=[])
    kg.create_entity(id=charlie_iri, types=[])
    
    # Create relations
    kg.create_relation(source=alice_iri, target=bob_iri, type=knows_iri)
    kg.create_relation(source=alice_iri, target=charlie_iri, type=knows_iri)
    
    # Get neighbors
    neighbors = kg.get_neighbors(entity_id=alice_iri, predicate=knows_iri)
    assert len(neighbors) == 2
    neighbor_ids = {n.id for n in neighbors}
    assert bob_iri in neighbor_ids
    assert charlie_iri in neighbor_ids
    
    kg.close()

