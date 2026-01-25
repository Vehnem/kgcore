"""
Serialization strategies for function parameters and results in KG tracking.

This module provides strategies for serializing function arguments and results
when tracking function calls in the knowledge graph.
"""

from enum import Enum
from typing import Any, Callable, Optional
import hashlib
import json


class SerializationStrategy(str, Enum):
    """
    Strategy for serializing function parameters and results.
    
    - FULL: Full JSON serialization (default, good for small data)
    - REFERENCE: Use instance IDs for tracked objects, references for others
    - SKIP: Don't serialize at all
    - HASH: Only store hash and size metadata
    - SAMPLE: Sample large collections (first, middle, last items)
    """

    FULL = "full"
    REFERENCE = "reference"
    SKIP = "skip"
    HASH = "hash"
    SAMPLE = "sample"


# Type alias for custom serialization functions
SerializationFunction = Callable[[Any], Optional[str]]


def serialize_value(
    value: Any,
    strategy: SerializationStrategy | str | SerializationFunction,
    max_size: int = 10000,
    context: str = "value",
) -> Optional[str]:
    """
    Serialize a value according to the specified strategy.
    
    Args:
        value: The value to serialize
        strategy: Serialization strategy (enum, string, or custom function)
        max_size: Maximum size in bytes before truncation/reference (for FULL)
        context: Context name for error messages (e.g., "arg[0]", "result")
    
    Returns:
        Serialized string representation, or None if SKIP strategy
    """
    # Handle custom callable strategy
    if callable(strategy) and not isinstance(strategy, type):
        try:
            return strategy(value)
        except Exception as e:
            # Fallback to FULL on error
            return _serialize_full(value, max_size)
    
    # Convert string to enum
    if isinstance(strategy, str):
        try:
            strategy = SerializationStrategy(strategy.lower())
        except ValueError:
            # Unknown strategy, default to FULL
            strategy = SerializationStrategy.FULL
    
    # Apply strategy
    if strategy == SerializationStrategy.SKIP:
        return None
    
    if strategy == SerializationStrategy.REFERENCE:
        return _serialize_reference(value)
    
    if strategy == SerializationStrategy.HASH:
        return _serialize_hash(value)
    
    if strategy == SerializationStrategy.SAMPLE:
        return _serialize_sample(value, max_size)
    
    if strategy == SerializationStrategy.FULL:
        return _serialize_full(value, max_size)
    
    # Default fallback
    return _serialize_full(value, max_size)


def _serialize_reference(value: Any) -> str:
    """Serialize using reference (instance ID or hash)."""
    # Check if it's a tracked instance with an ID
    if hasattr(value, "__kg_instance_id__"):
        return f"ref:instance:{value.__kg_instance_id__}"
    
    # Check if it's a Pydantic model (could create instance ID)
    if hasattr(value, "model_dump") and hasattr(value, "__class__"):
        # Try to generate deterministic ID using same logic as decorators
        try:
            attrs = {}
            for key, val in vars(value).items():
                if key.startswith("_"):
                    continue
                try:
                    json.dumps(val, default=str)
                    attrs[key] = val
                except (TypeError, ValueError):
                    attrs[key] = str(val)
            serialized = json.dumps(attrs, sort_keys=True, default=str)
            hash_val = hashlib.sha256(serialized.encode()).hexdigest()[:16]
            qualname = f"{type(value).__module__}.{type(value).__name__}"
            instance_id = f"sys:instance:{qualname}:{hash_val}"
            return f"ref:instance:{instance_id}"
        except Exception:
            pass
    
    # For other objects, use hash reference
    try:
        serialized = json.dumps(value, default=str)
        hash_val = hashlib.sha256(serialized.encode()).hexdigest()[:16]
        size = len(serialized.encode())
        return f"ref:hash:{hash_val}:size:{size}"
    except (TypeError, ValueError):
        # Non-serializable, use object ID
        return f"ref:object:{id(value)}"


def _serialize_hash(value: Any) -> str:
    """Serialize as hash and size metadata only."""
    try:
        serialized = json.dumps(value, default=str)
        size = len(serialized.encode('utf-8'))
        hash_val = hashlib.sha256(serialized.encode()).hexdigest()[:16]
        return f"hash:{hash_val}:size:{size}"
    except (TypeError, ValueError):
        # Non-serializable
        return f"hash:unserializable:{id(value)}"


def _serialize_sample(value: Any, max_items: int = 100) -> str:
    """Serialize with sampling for large collections."""
    if isinstance(value, list):
        if len(value) <= max_items:
            return json.dumps(value, default=str)
        
        # Sample: first, middle, last
        sample_size = max_items // 3
        sample = (
            value[:sample_size]
            + value[len(value) // 2 : len(value) // 2 + sample_size]
            + value[-sample_size:]
        )
        return json.dumps({
            "_type": "sampled_list",
            "total_length": len(value),
            "sample": sample,
        }, default=str)
    
    if isinstance(value, dict):
        if len(value) <= max_items:
            return json.dumps(value, default=str)
        
        # Sample first N items
        items = list(value.items())[:max_items]
        return json.dumps({
            "_type": "sampled_dict",
            "total_length": len(value),
            "sample": dict(items),
        }, default=str)
    
    # For non-collections, use full serialization
    return _serialize_full(value, max_size=10000)


def _serialize_full(value: Any, max_size: int = 10000) -> str:
    """Serialize fully, with truncation if too large."""
    try:
        serialized = json.dumps(value, default=str)
        size = len(serialized.encode('utf-8'))
        
        if size > max_size:
            # Truncate and add reference
            hash_val = hashlib.sha256(serialized.encode()).hexdigest()[:16]
            truncated = serialized[:max_size] + f"... [truncated, hash:{hash_val}, size:{size}]"
            return truncated
        
        return serialized
    except (TypeError, ValueError) as e:
        # Non-serializable, use string representation
        return f"<unserializable:{type(value).__name__}:{str(value)[:100]}>"

