# tests/test_smoke.py
from kgcore.api import KG

def test_memory_roundtrip():
    kg = KG()
    a = kg.create_entity(["A"], {"x": 1})
    b = kg.create_entity(["B"], {"y": 2})
    r = kg.create_relation("R", a.id, b.id, {"w": 3})
    kg.add_meta(a.id, {"m": 9})
    assert kg.find_entities("A")[0].props["x"] == 1
    assert kg.find_relations("R")[0].props["w"] == 3
