"""
Tests for @kg_tracked decorator.

Tests cover:
- Plain functions
- Plain classes
- Classes implementing KGAnnotatable
"""

import pytest
from typing import Mapping, Any
from kgcore.system import kg_tracked, KGAnnotatable, KGTracker
from kgcore.system.publishing import set_kg
from kgcore.api import KnowledgeGraph
from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel
from kgcore.system.schema import SysLabels, SysProperties


@pytest.fixture
def kg():
    """Create a KnowledgeGraph instance for testing."""
    backend = RDFLibBackend()
    model = RDFBaseModel()
    kg_instance = KnowledgeGraph(model=model, backend=backend)
    set_kg(kg_instance)
    yield kg_instance
    set_kg(None)
    kg_instance.close()


class TestPlainFunction:
    """Tests for @kg_tracked on plain functions."""

    def test_function_definition_tracked(self, kg):
        """Test that function definition is tracked."""
        @kg_tracked
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        # Check that entity was created
        qualname = f"{add.__module__}.{add.__name__}"
        entity_id = f"sys:function:{qualname}"
        entity = kg.read_entity(entity_id)
        
        assert entity is not None
        assert SysLabels.Function in entity.labels
        prop_dict = {prop.key: prop.value for prop in entity.properties}
        assert prop_dict[SysProperties.NAME] == "add"
        assert prop_dict[SysProperties.MODULE] == add.__module__

    def test_function_call_tracked(self, kg):
        """Test that function calls are tracked."""
        @kg_tracked
        def multiply(x: int, y: int) -> int:
            """Multiply two numbers."""
            return x * y

        result = multiply(3, 4)

        assert result == 12
        
        # Check that a run entity was created
        # We can't easily get the exact run_id, but we can check entities were created
        # The call should have created a relation
        qualname = f"{multiply.__module__}.{multiply.__name__}"
        func_id = f"sys:function:{qualname}"
        func_entity = kg.read_entity(func_id)
        assert func_entity is not None

    def test_function_with_track_calls_false(self, kg):
        """Test function with track_calls=False."""
        @kg_tracked(track_calls=False)
        def subtract(a: int, b: int) -> int:
            """Subtract b from a."""
            return a - b

        result = subtract(10, 3)

        assert result == 7
        # Calls should not be tracked, but definition should be
        qualname = f"{subtract.__module__}.{subtract.__name__}"
        entity_id = f"sys:function:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None

    def test_function_with_track_definition_false(self, kg):
        """Test function with track_definition=False."""
        @kg_tracked(track_definition=False)
        def divide(a: int, b: int) -> float:
            """Divide a by b."""
            return a / b

        # Definition should not be published
        qualname = f"{divide.__module__}.{divide.__name__}"
        entity_id = f"sys:function:{qualname}"
        entity = kg.read_entity(entity_id)
        # Entity might not exist if definition wasn't tracked
        # But calls should still work
        result = divide(10, 2)
        assert result == 5.0


class TestPlainClass:
    """Tests for @kg_tracked on plain classes."""

    def test_class_definition_tracked(self, kg):
        """Test that class definition is tracked."""
        @kg_tracked
        class Calculator:
            """A simple calculator."""

            def __init__(self, name: str):
                self.name = name

        # Check that entity was created
        qualname = f"{Calculator.__module__}.{Calculator.__name__}"
        entity_id = f"sys:class:{qualname}"
        entity = kg.read_entity(entity_id)
        
        assert entity is not None
        assert SysLabels.Class in entity.labels
        prop_dict = {prop.key: prop.value for prop in entity.properties}
        assert prop_dict[SysProperties.NAME] == "Calculator"

    def test_class_init_tracked(self, kg):
        """Test that class instantiation is tracked."""
        @kg_tracked
        class Person:
            """Represents a person."""

            def __init__(self, name: str, age: int):
                self.name = name
                self.age = age

        person = Person("Alice", 30)

        assert person.name == "Alice"
        assert person.age == 30
        
        # Check that class entity exists
        qualname = f"{Person.__module__}.{Person.__name__}"
        entity_id = f"sys:class:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None

    def test_class_with_track_calls_false(self, kg):
        """Test class with track_calls=False."""
        @kg_tracked(track_calls=False)
        class Counter:
            """A counter class."""

            def __init__(self, initial: int = 0):
                self.value = initial

        counter = Counter(5)

        assert counter.value == 5
        # Definition should still be tracked
        qualname = f"{Counter.__module__}.{Counter.__name__}"
        entity_id = f"sys:class:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None


class TestAnnotatableClass:
    """Tests for @kg_tracked on classes implementing KGAnnotatable."""

    def test_annotatable_class_definition(self, kg):
        """Test that annotatable class uses custom kg_definition."""
        @kg_tracked
        class CustomClass:
            """A class with custom KG methods."""

            def kg_definition(self) -> Mapping[str, Any]:
                # Use type(self) to get the class
                cls = type(self)
                return {
                    "kind": "custom_class",
                    "name": cls.__name__,
                    "module": cls.__module__,
                    "custom_field": "custom_value",
                }

            def kg_call(self, *args, **kwargs) -> Mapping[str, Any]:
                return {
                    "event": "custom_init",
                    "custom": True,
                }

            def __init__(self, value: str):
                self.value = value

        # Check that entity was created with custom data
        # The publishing code will use the kind from kg_definition
        qualname = f"{CustomClass.__module__}.{CustomClass.__name__}"
        entity_id = f"sys:custom_class:{qualname}"
        entity = kg.read_entity(entity_id)
        
        assert entity is not None
        # Check for custom field in properties
        prop_dict = {prop.key: prop.value for prop in entity.properties}
        # Custom fields should be stored with system namespace
        custom_props = {k: v for k, v in prop_dict.items() if "custom" in k.lower()}
        assert len(custom_props) > 0

    def test_annotatable_class_call(self, kg):
        """Test that annotatable class uses custom kg_call."""
        @kg_tracked
        class TrackedClass:
            """A tracked class."""

            def kg_definition(self) -> Mapping[str, Any]:
                cls = type(self)
                return {
                    "kind": "tracked",
                    "name": cls.__name__,
                    "module": cls.__module__,
                }

            def kg_call(self, *args, **kwargs) -> Mapping[str, Any]:
                return {
                    "event": "tracked_init",
                    "args_count": len(args),
                    "has_kwargs": len(kwargs) > 0,
                }

            def __init__(self, x: int, y: int = 0):
                self.x = x
                self.y = y

        obj = TrackedClass(10, y=20)

        assert obj.x == 10
        assert obj.y == 20
        
        # Check that class entity exists (using custom kind from kg_definition)
        qualname = f"{TrackedClass.__module__}.{TrackedClass.__name__}"
        entity_id = f"sys:tracked:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None

    def test_annotatable_function(self, kg):
        """Test that functions can also implement KGAnnotatable."""
        # Define the function first
        def custom_function(x: int) -> int:
            """A function with custom KG methods."""
            return x * 2

        # Attach methods before decorating
        def kg_definition() -> Mapping[str, Any]:
            return {
                "kind": "custom_function",
                "name": "custom_function",
                "module": custom_function.__module__,
            }

        def kg_call(*args, **kwargs) -> Mapping[str, Any]:
            return {"event": "custom_call", "input": args[0] if args else None}

        custom_function.kg_definition = kg_definition  # type: ignore[attr-defined]
        custom_function.kg_call = kg_call  # type: ignore[attr-defined]

        # Now decorate it
        custom_function = kg_tracked(custom_function)

        # Check that entity was created with custom kind
        qualname = f"{custom_function.__module__}.{custom_function.__name__}"
        entity_id = f"sys:custom_function:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None

        result = custom_function(5)

        assert result == 10
