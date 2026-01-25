"""
The main @kg_tracked decorator and any variants.

This module provides the primary decorator for tracking Python objects
in the knowledge graph.
"""

from functools import wraps
from typing import Any, Optional, Callable
import hashlib
import json

from .protocol import KGAnnotatable
from .tracker import KGTracker
from .introspection import (
    default_class_definition,
    default_function_definition,
    default_class_call,
    default_function_call,
)
from .publishing import publish_definition, publish_call
from .schema import SysProperties
from .serialization import (
    SerializationStrategy,
    SerializationFunction,
    serialize_value,
)
def _generate_instance_id(obj: Any, cls: type) -> str:
    """
    Deterministically generate an instance ID from the object's public attributes.
    Same attribute values -> same ID across runs.
    """
    attrs = {}
    for key, value in vars(obj).items():
        if key.startswith("_"):
            continue
        try:
            json.dumps(value, default=str)
            attrs[key] = value
        except (TypeError, ValueError):
            attrs[key] = str(value)

    serialized = json.dumps(attrs, sort_keys=True, default=str)
    hash_val = hashlib.sha256(serialized.encode()).hexdigest()[:16]
    qualname = f"{cls.__module__}.{cls.__name__}"
    return f"sys:instance:{qualname}:{hash_val}"



def kg_tracked(
    _obj=None,
    *,
    track_definition: bool = True,
    track_calls: bool = True,
    # Serialization strategies
    serialize_args: SerializationStrategy | str | SerializationFunction = SerializationStrategy.FULL,
    serialize_kwargs: SerializationStrategy | str | SerializationFunction = SerializationStrategy.FULL,
    serialize_result: SerializationStrategy | str | SerializationFunction = SerializationStrategy.FULL,
    # Size limits (for FULL and SAMPLE strategies)
    max_arg_size: int = 10000,      # bytes
    max_kwarg_size: int = 10000,    # bytes
    max_result_size: int = 10000,   # bytes
):
    """
    Decorator for classes/functions to track in the knowledge graph.
    
    Args:
        track_definition: Whether to track the definition
        track_calls: Whether to track calls/instantiations
        serialize_args: How to serialize positional arguments
        serialize_kwargs: How to serialize keyword arguments
        serialize_result: How to serialize return value
        max_*_size: Maximum size in bytes before truncation/reference (for FULL/SAMPLE)
    
    Serialization strategies:
        - SerializationStrategy.FULL: Full JSON serialization (default)
        - SerializationStrategy.REFERENCE: Use instance IDs/references
        - SerializationStrategy.SKIP: Don't serialize
        - SerializationStrategy.HASH: Only store hash and size
        - SerializationStrategy.SAMPLE: Sample large collections
        - Custom function: Callable[[Any], Optional[str]]
    
    Usage:
        @kg_tracked
        class Foo: ...

        @kg_tracked(track_calls=False)   # definition only
        def bar(): ...
        
        @kg_tracked(
            serialize_args=SerializationStrategy.REFERENCE,
            serialize_result=SerializationStrategy.SKIP
        )
        def process_large_data(df, config): ...
    """

    def decorator(obj):
        # initial flags; KGTracker can change these later
        setattr(obj, "__kg_track_definition__", track_definition)
        setattr(obj, "__kg_track_calls__", track_calls)
        
        # Store serialization strategies
        setattr(obj, "__kg_serialize_args__", serialize_args)
        setattr(obj, "__kg_serialize_kwargs__", serialize_kwargs)
        setattr(obj, "__kg_serialize_result__", serialize_result)
        setattr(obj, "__kg_max_arg_size__", max_arg_size)
        setattr(obj, "__kg_max_kwarg_size__", max_kwarg_size)
        setattr(obj, "__kg_max_result_size__", max_result_size)

        # ---------- annotatable path ----------
        if hasattr(obj, "kg_definition") and hasattr(obj, "kg_call"):
            # Definition
            if KGTracker.definition_enabled(obj):
                # For classes, handle instance methods specially
                if isinstance(obj, type):
                    kg_def = getattr(obj, "kg_definition")
                    # Try to call it - if it's an instance method, create a temp instance
                    try:
                        # First try calling directly (works for classmethods/staticmethods)
                        data = kg_def()  # type: ignore[call-arg]
                    except TypeError:
                        # It's an instance method, create a temporary instance
                        # Use object.__new__ to avoid calling __init__
                        try:
                            temp_instance = object.__new__(obj)
                            data = kg_def(temp_instance)  # type: ignore[call-arg]
                        except Exception:
                            # Last resort: try as unbound method
                            if hasattr(kg_def, "__func__"):
                                data = kg_def.__func__(obj)  # type: ignore[attr-defined]
                            else:
                                raise
                else:
                    # For functions, call directly
                    data = obj.kg_definition()  # type: ignore[attr-defined]
                publish_definition(data)

            # Classes (patch __init__)
            if isinstance(obj, type):
                orig_init = obj.__init__

                @wraps(orig_init)
                def __init__(self, *args, **kwargs):
                    orig_init(self, *args, **kwargs)
                    # Determine instance ID
                    instance_id: Optional[str] = None
                    if hasattr(self, "kg_id"):
                        try:
                            instance_id = self.kg_id()  # type: ignore[attr-defined]
                        except Exception:
                            instance_id = None
                    if instance_id is None:
                        instance_id = _generate_instance_id(self, obj)
                    setattr(self, "__kg_instance_id__", instance_id)
                    attributes = {k: v for k, v in vars(self).items() if not k.startswith("_")}
                    if KGTracker.calls_enabled(obj):
                        event = obj.kg_call(self, *args, **kwargs)  # type: ignore[attr-defined]
                        # Attach instance metadata
                        event["instance_id"] = instance_id
                        event["class_id"] = f"sys:class:{obj.__module__}.{obj.__name__}"
                        event["attributes"] = attributes
                        publish_call(event)

                obj.__init__ = __init__
                return obj

            # Functions
            if callable(obj):
                @wraps(obj)
                def wrapper(*args, **kwargs):
                    result = obj(*args, **kwargs)
                    if KGTracker.calls_enabled(wrapper):
                        event = obj.kg_call(*args, **kwargs)  # type: ignore[attr-defined]
                        # Apply serialization strategies if not already applied
                        if "args" in event and not isinstance(event["args"], str):
                            event["args"] = [
                                serialize_value(
                                    arg,
                                    serialize_args,
                                    max_arg_size,
                                    f"arg[{i}]"
                                )
                                for i, arg in enumerate(event["args"])
                            ]
                        if "kwargs" in event and not isinstance(event["kwargs"], str):
                            event["kwargs"] = {
                                k: serialize_value(
                                    v,
                                    serialize_kwargs,
                                    max_kwarg_size,
                                    f"kwarg:{k}"
                                )
                                for k, v in event["kwargs"].items()
                            }
                        if "result" in event and not isinstance(event["result"], str):
                            event["result"] = serialize_value(
                                event["result"],
                                serialize_result,
                                max_result_size,
                                "result"
                            )
                        publish_call(event)
                    return result

                # keep flags on wrapper
                setattr(wrapper, "__kg_track_definition__", track_definition)
                setattr(wrapper, "__kg_track_calls__", track_calls)
                setattr(wrapper, "__kg_serialize_args__", serialize_args)
                setattr(wrapper, "__kg_serialize_kwargs__", serialize_kwargs)
                setattr(wrapper, "__kg_serialize_result__", serialize_result)
                setattr(wrapper, "__kg_max_arg_size__", max_arg_size)
                setattr(wrapper, "__kg_max_kwarg_size__", max_kwarg_size)
                setattr(wrapper, "__kg_max_result_size__", max_result_size)
                return wrapper

        # ---------- fallback: plain class ----------
        if isinstance(obj, type):
            if KGTracker.definition_enabled(obj):
                publish_definition(default_class_definition(obj))

            orig_init = obj.__init__

            @wraps(orig_init)
            def __init__(self, *args, **kwargs):
                orig_init(self, *args, **kwargs)
                # Determine instance ID
                instance_id = _generate_instance_id(self, obj)
                setattr(self, "__kg_instance_id__", instance_id)
                attributes = {k: v for k, v in vars(self).items() if not k.startswith("_")}
                if KGTracker.calls_enabled(obj):
                    event = default_class_call(self, *args, **kwargs)
                    event["instance_id"] = instance_id
                    event["class_id"] = f"sys:class:{obj.__module__}.{obj.__name__}"
                    event["attributes"] = attributes
                    publish_call(event)

            obj.__init__ = __init__
            return obj

        # ---------- fallback: plain function ----------
        if callable(obj):
            if KGTracker.definition_enabled(obj):
                publish_definition(default_function_definition(obj))

            @wraps(obj)
            def wrapper(*args, **kwargs):
                result = obj(*args, **kwargs)
                if KGTracker.calls_enabled(wrapper):
                    event = default_function_call(obj, *args, result=result, **kwargs)
                    # Apply serialization strategies
                    if "args" in event:
                        event["args"] = [
                            serialize_value(
                                arg,
                                serialize_args,
                                max_arg_size,
                                f"arg[{i}]"
                            )
                            for i, arg in enumerate(event["args"])
                        ]
                    if "kwargs" in event:
                        event["kwargs"] = {
                            k: serialize_value(
                                v,
                                serialize_kwargs,
                                max_kwarg_size,
                                f"kwarg:{k}"
                            )
                            for k, v in event["kwargs"].items()
                        }
                    if "result" in event:
                        event["result"] = serialize_value(
                            event["result"],
                            serialize_result,
                            max_result_size,
                            "result"
                        )
                    publish_call(event)
                return result

            setattr(wrapper, "__kg_track_definition__", track_definition)
            setattr(wrapper, "__kg_track_calls__", track_calls)
            setattr(wrapper, "__kg_serialize_args__", serialize_args)
            setattr(wrapper, "__kg_serialize_kwargs__", serialize_kwargs)
            setattr(wrapper, "__kg_serialize_result__", serialize_result)
            setattr(wrapper, "__kg_max_arg_size__", max_arg_size)
            setattr(wrapper, "__kg_max_kwarg_size__", max_kwarg_size)
            setattr(wrapper, "__kg_max_result_size__", max_result_size)
            return wrapper

        raise TypeError(f"Unsupported object type for @kg_tracked: {obj!r}")

    # Support bare and configured usage
    if _obj is None:
        return decorator
    else:
        return decorator(_obj)


# Optional convenience decorators
def kg_node(cls=None, **kwargs):
    """Convenience decorator for classes."""
    return kg_tracked(cls, **kwargs)


def kg_function(fn=None, **kwargs):
    """Convenience decorator for functions."""
    return kg_tracked(fn, **kwargs)
