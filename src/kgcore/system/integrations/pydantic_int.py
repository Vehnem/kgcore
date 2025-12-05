"""
Ready-made helpers for Pydantic models that want to be KGAnnotatable.

This module provides a mixin class that Pydantic models can inherit from
to automatically implement the KGAnnotatable protocol.
"""

from typing import Mapping, Any
from pydantic import BaseModel


class PydanticKGMixin:
    """
    Mixin for Pydantic models to implement KGAnnotatable.
    
    Usage:
        from kgcore.system import kg_tracked
        from kgcore.system.integrations.pydantic import PydanticKGMixin
        from pydantic import BaseModel
        
        @kg_tracked
        class User(PydanticKGMixin, BaseModel):
            id: int
            name: str
    """

    def kg_definition(self) -> Mapping[str, Any]:
        """
        Extract KG definition from Pydantic model.
        
        Returns:
            Dictionary containing model metadata including fields
        """
        if not isinstance(self, BaseModel):
            raise TypeError("PydanticKGMixin requires a Pydantic BaseModel")

        model = type(self)
        fields_info = {}
        
        for name, field in model.model_fields.items():
            field_info: dict[str, Any] = {
                "type": str(field.annotation) if hasattr(field, "annotation") else "Any",
            }
            
            # Add default if present
            if hasattr(field, "default") and field.default is not ...:
                field_info["default"] = field.default
            
            # Add description if present
            if hasattr(field, "description") and field.description:
                field_info["description"] = field.description
            
            fields_info[name] = field_info

        return {
            "kind": "pydantic_model",
            "name": model.__name__,
            "module": model.__module__,
            "doc": model.__doc__,
            "fields": fields_info,
        }

    def kg_call(self, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
        """
        Extract KG call data from Pydantic instance creation.
        
        Args:
            *args: Positional arguments (typically self for instance methods)
            **kwargs: Keyword arguments passed during initialization
        
        Returns:
            Dictionary containing call event metadata
        """
        return {
            "event": "pydantic_init",
            "model": type(self).__name__,
            "module": type(self).__module__,
            "data": self.model_dump() if hasattr(self, "model_dump") else {},
        }

