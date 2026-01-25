"""
System Graph - Track Python code semantics and execution using Knowledge Graph API.

This module provides functionality to track Python code objects (functions, classes)
and their execution runs in a knowledge graph.
"""

# Public API - re-export main components
from .decorators import kg_tracked, kg_node, kg_function
from .protocol import KGAnnotatable
from .tracker import KGTracker
from .publishing import set_kg, get_kg, publish_definition, publish_call
from .schema import SysLabels, SysProperties
from .serialization import SerializationStrategy

__all__ = [
    "kg_tracked",
    "kg_node",
    "kg_function",
    "KGAnnotatable",
    "KGTracker",
    "set_kg",
    "get_kg",
    "publish_definition",
    "publish_call",
    "SysLabels",
    "SysProperties",
    "SerializationStrategy",
]
