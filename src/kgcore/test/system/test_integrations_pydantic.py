"""
Tests for Pydantic integration with KG tracking.

Tests verify that PydanticKGMixin works correctly with @kg_tracked decorator.
"""

import pytest
from pydantic import BaseModel, Field
from kgcore.system import kg_tracked
from kgcore.system.integrations import PydanticKGMixin
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


class TestPydanticKGMixin:
    """Tests for PydanticKGMixin."""

    def test_pydantic_model_with_mixin(self, kg):
        """Test that Pydantic model with mixin implements KGAnnotatable."""
        @kg_tracked
        class User(PydanticKGMixin, BaseModel):
            """User model."""

            id: int
            name: str
            email: str

        # Check that entity was created
        qualname = f"{User.__module__}.{User.__name__}"
        entity_id = f"sys:pydantic:{qualname}"
        entity = kg.read_entity(entity_id)
        
        assert entity is not None
        assert SysLabels.PydanticModel in entity.labels
        prop_dict = {prop.key: prop.value for prop in entity.properties}
        assert prop_dict[SysProperties.NAME] == "User"

    def test_pydantic_model_fields_metadata(self, kg):
        """Test that field metadata is captured correctly."""
        @kg_tracked
        class Product(PydanticKGMixin, BaseModel):
            """Product model."""

            name: str = Field(description="Product name")
            price: float = Field(description="Product price", default=0.0)
            in_stock: bool = Field(default=True)

        # Check field metadata
        qualname = f"{Product.__module__}.{Product.__name__}"
        entity_id = f"sys:pydantic:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None
        
        prop_dict = {prop.key: prop.value for prop in entity.properties}
        # Fields should be stored as JSON
        assert any("fields" in key.lower() for key in prop_dict.keys())

    def test_pydantic_model_init_tracking(self, kg):
        """Test that Pydantic model instantiation is tracked."""
        @kg_tracked
        class Person(PydanticKGMixin, BaseModel):
            """Person model."""

            name: str
            age: int

        person = Person(name="Alice", age=30)

        assert person.name == "Alice"
        assert person.age == 30
        
        # Check that model entity exists
        qualname = f"{Person.__module__}.{Person.__name__}"
        entity_id = f"sys:pydantic:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None

    def test_pydantic_model_with_defaults(self, kg):
        """Test Pydantic model with default values."""
        @kg_tracked
        class Config(PydanticKGMixin, BaseModel):
            """Configuration model."""

            host: str = "localhost"
            port: int = 8080
            debug: bool = False

        # Check that defaults are captured
        qualname = f"{Config.__module__}.{Config.__name__}"
        entity_id = f"sys:pydantic:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None

        # Create instance with defaults
        config = Config()

        assert config.host == "localhost"
        assert config.port == 8080
        assert config.debug is False

    def test_pydantic_model_with_optional_fields(self, kg):
        """Test Pydantic model with optional fields."""
        from typing import Optional

        @kg_tracked
        class Profile(PydanticKGMixin, BaseModel):
            """User profile."""

            username: str
            bio: Optional[str] = None
            avatar_url: Optional[str] = None

        qualname = f"{Profile.__module__}.{Profile.__name__}"
        entity_id = f"sys:pydantic:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None

        # Create instance
        profile = Profile(username="alice", bio="Developer")

        assert profile.username == "alice"
        assert profile.bio == "Developer"
        assert profile.avatar_url is None

    def test_pydantic_mixin_without_base_model_raises(self):
        """Test that PydanticKGMixin raises error if not used with BaseModel."""
        # This should raise an error when kg_definition is called
        class NotPydantic(PydanticKGMixin):
            """Not a Pydantic model."""

            pass

        with pytest.raises(TypeError, match="PydanticKGMixin requires a Pydantic BaseModel"):
            NotPydantic().kg_definition()

    def test_pydantic_model_docstring(self, kg):
        """Test that model docstring is captured."""
        @kg_tracked
        class Document(PydanticKGMixin, BaseModel):
            """A document model for testing."""

            title: str
            content: str

        qualname = f"{Document.__module__}.{Document.__name__}"
        entity_id = f"sys:pydantic:{qualname}"
        entity = kg.read_entity(entity_id)
        assert entity is not None
        
        prop_dict = {prop.key: prop.value for prop in entity.properties}
        assert SysProperties.DESCRIPTION in prop_dict or any("doc" in key.lower() for key in prop_dict.keys())

    def test_multiple_pydantic_models(self, kg):
        """Test multiple Pydantic models can be tracked."""
        @kg_tracked
        class ModelA(PydanticKGMixin, BaseModel):
            """Model A."""

            field_a: str

        @kg_tracked
        class ModelB(PydanticKGMixin, BaseModel):
            """Model B."""

            field_b: int

        # Both definitions should be captured
        qualname_a = f"{ModelA.__module__}.{ModelA.__name__}"
        qualname_b = f"{ModelB.__module__}.{ModelB.__name__}"
        entity_a = kg.read_entity(f"sys:pydantic:{qualname_a}")
        entity_b = kg.read_entity(f"sys:pydantic:{qualname_b}")
        
        assert entity_a is not None
        assert entity_b is not None

        # Create instances
        a = ModelA(field_a="test")
        b = ModelB(field_b=42)

        assert a.field_a == "test"
        assert b.field_b == 42
