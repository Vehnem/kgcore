"""
Base handler abstractions (optional strategy pattern).

This module provides base classes for handler implementations.
Handlers are optional - the decorator can work directly with protocol + introspection.
"""

from typing import Protocol, Any


class KGHandler(Protocol):
    """
    Protocol for handlers that process KG tracking for objects.
    
    Handlers can customize how definitions and calls are processed.
    This is only needed if you want a pluggable handler strategy.
    """

    def on_definition(self, obj: Any) -> None:
        """
        Process definition metadata for an object.
        
        Args:
            obj: The object to process
        """
        ...

    def wrap_for_calls(self, obj: Any) -> Any:
        """
        Wrap an object to track calls.
        
        Args:
            obj: The object to wrap
            
        Returns:
            The wrapped object
        """
        ...

