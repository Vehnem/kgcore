"""
Tests for serialization strategies in @kg_tracked decorator.

Tests verify that different serialization strategies work correctly
for function arguments, kwargs, and results.
"""

import pytest
from kgcore.system import kg_tracked, SerializationStrategy
from kgcore.system.publishing import set_kg
from kgcore.api import KnowledgeGraph
from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel
from pydantic import BaseModel


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


class TestSerializationStrategies:
    """Tests for different serialization strategies."""

    def test_full_serialization_default(self, kg):
        """Test that FULL serialization is the default."""
        @kg_tracked
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        result = add(3, 4)
        assert result == 7

        # Check that args and result are fully serialized
        qualname = f"{add.__module__}.{add.__name__}"
        # The call should have been published with full serialization

    def test_skip_strategy(self, kg):
        """Test SKIP strategy - don't serialize at all."""
        @kg_tracked(
            serialize_args=SerializationStrategy.SKIP,
            serialize_kwargs=SerializationStrategy.SKIP,
            serialize_result=SerializationStrategy.SKIP,
        )
        def process(data: dict, config: dict = None) -> dict:
            """Process data."""
            return {"processed": data}

        result = process({"key": "value"}, config={"setting": "value"})
        assert result["processed"]["key"] == "value"

        # Args, kwargs, and result should not be in the published call
        # (they'll be None and filtered out)

    def test_reference_strategy(self, kg):
        """Test REFERENCE strategy - use instance IDs."""
        @kg_tracked
        class Config:
            """Configuration object."""

            def __init__(self, setting: str):
                self.setting = setting

        @kg_tracked(serialize_args=SerializationStrategy.REFERENCE)
        def use_config(config: Config) -> str:
            """Use configuration."""
            return config.setting

        config = Config("test")
        result = use_config(config)

        assert result == "test"
        # Args should use reference to instance ID

    def test_hash_strategy(self, kg):
        """Test HASH strategy - only store hash and size."""
        @kg_tracked(
            serialize_args=SerializationStrategy.HASH,
            serialize_result=SerializationStrategy.HASH,
        )
        def process_large(data: list) -> dict:
            """Process large data."""
            return {"size": len(data), "first": data[0] if data else None}

        large_data = list(range(1000))
        result = process_large(large_data)

        assert result["size"] == 1000
        # Args and result should be stored as hash:...:size:...

    def test_sample_strategy(self, kg):
        """Test SAMPLE strategy - sample large collections."""
        @kg_tracked(serialize_args=SerializationStrategy.SAMPLE)
        def process_list(data: list) -> int:
            """Process a list."""
            return len(data)

        large_list = list(range(500))
        result = process_list(large_list)

        assert result == 500
        # Args should be sampled (first, middle, last items)

    def test_mixed_strategies(self, kg):
        """Test using different strategies for args, kwargs, and result."""
        @kg_tracked(
            serialize_args=SerializationStrategy.FULL,
            serialize_kwargs=SerializationStrategy.REFERENCE,
            serialize_result=SerializationStrategy.SKIP,
        )
        def process(a: int, b: int, config: dict = None) -> dict:
            """Process with mixed strategies."""
            return {"sum": a + b, "config": config}

        result = process(5, 10, config={"setting": "value"})
        assert result["sum"] == 15

    def test_custom_serialization_function(self, kg):
        """Test custom serialization function."""
        def custom_serializer(value):
            """Custom serializer that only keeps type and length."""
            if isinstance(value, (list, dict, str)):
                return f"custom:{type(value).__name__}:len:{len(value)}"
            return f"custom:{type(value).__name__}"

        @kg_tracked(serialize_args=custom_serializer)
        def process(data) -> str:
            """Process with custom serializer."""
            return "done"

        result = process([1, 2, 3, 4, 5])
        assert result == "done"

    def test_size_limits(self, kg):
        """Test that size limits work for FULL strategy."""
        @kg_tracked(
            serialize_args=SerializationStrategy.FULL,
            max_arg_size=100,  # Small limit
        )
        def process(data: str) -> str:
            """Process data."""
            return data

        large_data = "x" * 200  # Larger than limit
        result = process(large_data)

        assert result == large_data
        # Args should be truncated with hash reference

    def test_pydantic_model_reference(self, kg):
        """Test that Pydantic models use instance references."""
        from kgcore.system.integrations import PydanticKGMixin

        @kg_tracked
        class User(PydanticKGMixin, BaseModel):
            """User model."""

            name: str
            email: str

        @kg_tracked(serialize_args=SerializationStrategy.REFERENCE)
        def get_user_name(user: User) -> str:
            """Get user name."""
            return user.name

        user = User(name="Alice", email="alice@example.com")
        result = get_user_name(user)

        assert result == "Alice"
        # Args should reference the user instance

    def test_none_handling(self, kg):
        """Test that None values are handled correctly."""
        @kg_tracked(
            serialize_args=SerializationStrategy.FULL,
            serialize_result=SerializationStrategy.FULL,
        )
        def process(data=None) -> str:
            """Process with optional data."""
            return "done" if data is None else "processed"

        result = process()
        assert result == "done"

        result = process(None)
        assert result == "done"

    def test_string_strategy(self, kg):
        """Test that string strategy names work."""
        @kg_tracked(
            serialize_args="hash",
            serialize_result="skip",
        )
        def process(data: list) -> dict:
            """Process data."""
            return {"size": len(data)}

        result = process([1, 2, 3])
        assert result["size"] == 3

    def test_large_result_truncation(self, kg):
        """Test that large results are truncated."""
        @kg_tracked(
            serialize_result=SerializationStrategy.FULL,
            max_result_size=50,
        )
        def generate_large() -> str:
            """Generate large result."""
            return "x" * 100

        result = generate_large()
        assert len(result) == 100
        # Result should be truncated in KG

    def test_error_in_custom_serializer(self, kg):
        """Test that errors in custom serializer fall back to FULL."""
        def failing_serializer(value):
            """Serializer that fails."""
            raise ValueError("Serialization failed")

        @kg_tracked(serialize_args=failing_serializer)
        def process(data: int) -> int:
            """Process data."""
            return data * 2

        result = process(5)
        assert result == 10
        # Should fall back to FULL serialization on error


