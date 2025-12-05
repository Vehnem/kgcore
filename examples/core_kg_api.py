"""
Example of using the core knowledge graph API.
"""

from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel
from kgcore.api import KnowledgeGraph, KGProperty

# Create backend and model
backend = RDFLibBackend()
model = RDFBaseModel()
kg = KnowledgeGraph(model=model, backend=backend)

# Use full IRIs for the sketch
alice_iri = "http://example.org/Alice"
person_iri = "http://example.org/Person"
name_prop_iri = "http://example.org/name"
knows_iri = "http://example.org/knows"
bob_iri = "http://example.org/Bob"

# Create entities with properties
alice = kg.create_entity(
    id=alice_iri,
    types=[person_iri],
    properties=[KGProperty(key=name_prop_iri, value="Alice")],
)
print(f"Created entity: {alice}")

bob = kg.create_entity(
    id=bob_iri,
    types=[person_iri],
    properties=[KGProperty(key=name_prop_iri, value="Bob")],
)
print(f"Created entity: {bob}")

# Create a relation
relation = kg.create_relation(
    source=alice_iri,
    target=bob_iri,
    type=knows_iri,
)
print(f"Created relation: {relation}")

# Read entity back
print("\nAlice entity view:")
alice_data = kg.read_entity(alice_iri)
print(alice_data)

# Get neighbors
print("\nAlice neighbors via ex:knows:")
neighbors = kg.get_neighbors(entity_id=alice_iri, predicate=knows_iri)
for neighbor in neighbors:
    print(f"  - {neighbor}")

# Clean up
kg.close()
