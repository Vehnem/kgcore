# examples/01_minimal_inmemory.py
from kgcore.api import KG

kg = KG()
a = kg.create_entity(["Person"], {"name": "Ada"})
b = kg.create_entity(["Person"], {"name": "Charles"})
r = kg.create_relation("KNOWS", a.id, b.id, {"since": 1843})
kg.add_meta(r.id, {"confidence": 0.9})
print("Entities:", [e.props for e in kg.find_entities("Person")])
print("Relations:", [r.type for r in kg.find_relations("KNOWS")])
