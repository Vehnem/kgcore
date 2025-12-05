"""
Tests for KGTracker enable/disable functionality.

Tests verify that KGTracker can toggle tracking behavior on decorated objects.
"""

import pytest
from kgcore.system import kg_tracked, KGTracker
from kgcore.system.publishing import set_kg
from kgcore.api import KnowledgeGraph
from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel


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


class TestTrackerDisableEnable:
    """Tests for KGTracker.disable and KGTracker.enable."""

    def test_disable_calls(self, kg):
        """Test disabling call tracking."""
        @kg_tracked
        def test_func(x: int) -> int:
            """Test function."""
            return x * 2

        # Initially calls should be tracked
        result = test_func(5)
        assert result == 10

        # Disable calls
        KGTracker.disable(test_func, calls=True)
        
        # Now calls should not be tracked (but function should still work)
        result = test_func(10)
        assert result == 20

    def test_enable_calls(self, kg):
        """Test re-enabling call tracking."""
        @kg_tracked
        def test_func(x: int) -> int:
            """Test function."""
            return x + 1

        # Disable first
        KGTracker.disable(test_func, calls=True)
        result = test_func(5)
        assert result == 6

        # Re-enable
        KGTracker.enable(test_func, calls=True)
        result = test_func(10)
        assert result == 11

    def test_disable_definition(self, kg):
        """Test disabling definition tracking."""
        # Create a new decorated function
        @kg_tracked
        def new_func(x: int) -> int:
            """New function."""
            return x

        # Disable definition tracking
        KGTracker.disable(new_func, definition=True)

        # Verify flag is set
        assert KGTracker.definition_enabled(new_func) is False

    def test_disable_both(self, kg):
        """Test disabling both calls and definition."""
        @kg_tracked
        class TestClass:
            """Test class."""

            def __init__(self, value: int):
                self.value = value

        # Disable both
        KGTracker.disable(TestClass, calls=True, definition=True)

        # Verify flags
        assert KGTracker.calls_enabled(TestClass) is False
        assert KGTracker.definition_enabled(TestClass) is False

        # Create instance - should still work
        obj = TestClass(42)
        assert obj.value == 42

    def test_enable_both(self, kg):
        """Test enabling both calls and definition."""
        @kg_tracked
        class TestClass:
            """Test class."""

            def __init__(self, value: str):
                self.value = value

        # Disable both first
        KGTracker.disable(TestClass, calls=True, definition=True)
        assert KGTracker.calls_enabled(TestClass) is False
        assert KGTracker.definition_enabled(TestClass) is False

        # Re-enable both
        KGTracker.enable(TestClass, calls=True, definition=True)
        assert KGTracker.calls_enabled(TestClass) is True
        assert KGTracker.definition_enabled(TestClass) is True

    def test_calls_enabled_default(self, kg):
        """Test that calls_enabled returns True by default."""
        @kg_tracked
        def test_func(x: int) -> int:
            """Test function."""
            return x

        # Should be enabled by default
        assert KGTracker.calls_enabled(test_func) is True

    def test_definition_enabled_default(self, kg):
        """Test that definition_enabled returns True by default."""
        @kg_tracked
        class TestClass:
            """Test class."""

            pass

        # Should be enabled by default
        assert KGTracker.definition_enabled(TestClass) is True

    def test_track_calls_false_then_enable(self, kg):
        """Test enabling calls on a function decorated with track_calls=False."""
        @kg_tracked(track_calls=False)
        def test_func(x: int) -> int:
            """Test function."""
            return x * 3

        # Initially disabled
        assert KGTracker.calls_enabled(test_func) is False
        result = test_func(5)
        assert result == 15

        # Enable it
        KGTracker.enable(test_func, calls=True)
        result = test_func(10)
        assert result == 30

    def test_track_definition_false_then_enable(self, kg):
        """Test enabling definition on a function decorated with track_definition=False."""
        @kg_tracked(track_definition=False)
        def test_func(x: int) -> int:
            """Test function."""
            return x

        # Initially disabled
        assert KGTracker.definition_enabled(test_func) is False

        # Enable it (but definition is only published at decoration time)
        KGTracker.enable(test_func, definition=True)
        assert KGTracker.definition_enabled(test_func) is True

    def test_class_instance_tracking(self, kg):
        """Test that disabling on class affects instances."""
        @kg_tracked
        class TestClass:
            """Test class."""

            def __init__(self, value: int):
                self.value = value

        # Disable on class
        KGTracker.disable(TestClass, calls=True)

        # Create instance - should still work
        obj = TestClass(100)
        assert obj.value == 100

        # Re-enable
        KGTracker.enable(TestClass, calls=True)

        # Create another instance - should still work
        obj2 = TestClass(200)
        assert obj2.value == 200
