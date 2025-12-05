"""
Abstraction for writing into the KG backend using the KnowledgeGraph API.

This module provides the publishing interface for writing definition and call
metadata into the knowledge graph using the existing KnowledgeGraph API.
"""

from typing import Mapping, Any, Optional
from datetime import datetime, timezone
from uuid import uuid4
import hashlib
import json

from kgcore.api import KnowledgeGraph, KGEntity, KGProperty
from kgcore.system.schema import SysLabels, SysProperties


# Global KnowledgeGraph instance (set by user)
_default_kg: Optional[KnowledgeGraph] = None


def set_kg(kg: KnowledgeGraph) -> None:
    """
    Set the default global KnowledgeGraph instance.
    
    Args:
        kg: The KnowledgeGraph instance to use for publishing
    """
    global _default_kg
    _default_kg = kg


def get_kg() -> Optional[KnowledgeGraph]:
    """
    Get the current default KnowledgeGraph instance.
    
    Returns:
        The current KnowledgeGraph instance, or None if not set
    """
    return _default_kg


def publish_definition(data: Mapping[str, Any]) -> None:
    """
    Publish class/function definition to KG.
    
    This converts the introspection data into KGEntity and stores it
    using the KnowledgeGraph API.
    
    Args:
        data: Dictionary containing definition metadata (kind, name, module, etc.)
    """
    kg = _get_kg()
    if not kg:
        return
    
    kind = data.get("kind", "unknown")
    name = data.get("name", "unknown")
    module = data.get("module", "unknown")
    
    # Build entity ID
    qualname = f"{module}.{name}"
    if kind == "class":
        entity_id = f"sys:class:{qualname}"
        labels = [SysLabels.CodeObject, SysLabels.Class]
    elif kind == "function":
        entity_id = f"sys:function:{qualname}"
        labels = [SysLabels.CodeObject, SysLabels.Function]
    elif kind == "pydantic_model":
        entity_id = f"sys:pydantic:{qualname}"
        labels = [SysLabels.CodeObject, SysLabels.Class, SysLabels.PydanticModel]
    else:
        entity_id = f"sys:{kind}:{qualname}"
        labels = [SysLabels.CodeObject]
    
    # Build properties
    properties = [
        KGProperty(key=SysProperties.QUALNAME, value=qualname),
        KGProperty(key=SysProperties.NAME, value=name),
        KGProperty(key=SysProperties.MODULE, value=module),
    ]
    
    if "doc" in data and data["doc"]:
        properties.append(KGProperty(key=SysProperties.DESCRIPTION, value=data["doc"]))
    
    # Add kind-specific properties
    if "signature" in data:
        properties.append(KGProperty(key="http://kgcore.org/system/signature", value=data["signature"]))
    
    if "bases" in data and data["bases"]:
        properties.append(KGProperty(key="http://kgcore.org/system/bases", value=json.dumps(data["bases"])))
    
    if "fields" in data:
        # For Pydantic models, store field information
        # Clean fields to remove non-serializable values
        clean_fields = {}
        for field_name, field_info in data["fields"].items():
            clean_info = {}
            for k, v in field_info.items():
                # Skip PydanticUndefinedType and other non-serializable values
                try:
                    json.dumps(v)
                    clean_info[k] = v
                except (TypeError, ValueError):
                    # Skip non-serializable values
                    pass
            clean_fields[field_name] = clean_info
        properties.append(KGProperty(key="http://kgcore.org/system/fields", value=json.dumps(clean_fields)))
    
    # Add any additional metadata
    for key, value in data.items():
        if key not in ("kind", "name", "module", "doc", "signature", "bases", "fields"):
            # Convert non-string values to JSON
            if not isinstance(value, str):
                value = json.dumps(value)
            properties.append(KGProperty(key=f"http://kgcore.org/system/{key}", value=value))
    
    # Create or update entity
    try:
        existing = kg.read_entity(entity_id)
        if existing:
            # Update existing entity
            updated = KGEntity(
                id=entity_id,
                labels=labels,
                properties=properties,
            )
            kg.update_entity(updated)
        else:
            # Create new entity
            kg.create_entity(
                id=entity_id,
                types=labels,
                properties=properties,
            )
    except Exception:
        # If update fails, try to create
        try:
            kg.create_entity(
                id=entity_id,
                types=labels,
                properties=properties,
            )
        except Exception:
            # Silently fail if KG is not available
            pass


def publish_call(data: Mapping[str, Any]) -> None:
    """
    Publish call/init event to KG.
    
    This converts the call data into KGEntity and stores it
    using the KnowledgeGraph API.
    
    Args:
        data: Dictionary containing call event metadata (event, function/class, args, etc.)
    """
    kg = _get_kg()
    if not kg:
        return
    
    event_type = data.get("event", "unknown")
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Create run ID
    run_id = f"sys:run:{uuid4().hex[:16]}"
    
    # Build properties
    properties = [
        KGProperty(key=SysProperties.TIMESTAMP, value=timestamp),
        KGProperty(key=SysProperties.STATUS, value="completed"),
    ]
    
    # Add event-specific data
    if "class" in data:
        properties.append(KGProperty(key="http://kgcore.org/system/class", value=data["class"]))
        func_qualname = f"{data.get('module', 'unknown')}.{data['class']}"
        func_id = f"sys:class:{func_qualname}"
        class_id = func_id
    elif "function" in data:
        properties.append(KGProperty(key="http://kgcore.org/system/function", value=data["function"]))
        func_qualname = f"{data.get('module', 'unknown')}.{data['function']}"
        func_id = f"sys:function:{func_qualname}"
        class_id = None
    elif "model" in data:
        properties.append(KGProperty(key="http://kgcore.org/system/model", value=data["model"]))
        func_qualname = f"{data.get('module', 'unknown')}.{data['model']}"
        func_id = f"sys:pydantic:{func_qualname}"
        class_id = func_id
    else:
        func_id = None
        class_id = None
    
    # Add args and kwargs (may be None if SKIP strategy was used)
    if "args" in data and data["args"] is not None:
        # Args may be a list of serialized strings or None values
        args_value = data["args"]
        if isinstance(args_value, list):
            # Filter out None values (from SKIP strategy)
            filtered_args = [a for a in args_value if a is not None]
            if filtered_args:
                properties.append(KGProperty(key="http://kgcore.org/system/arguments", value=json.dumps(filtered_args)))
        else:
            properties.append(KGProperty(key="http://kgcore.org/system/arguments", value=json.dumps(args_value)))
    
    if "kwargs" in data and data["kwargs"] is not None:
        # Kwargs may be a dict with None values (from SKIP strategy)
        kwargs_value = data["kwargs"]
        if isinstance(kwargs_value, dict):
            # Filter out None values
            filtered_kwargs = {k: v for k, v in kwargs_value.items() if v is not None}
            if filtered_kwargs:
                properties.append(KGProperty(key="http://kgcore.org/system/keywordArguments", value=json.dumps(filtered_kwargs)))
        else:
            properties.append(KGProperty(key="http://kgcore.org/system/keywordArguments", value=json.dumps(kwargs_value)))
    
    # Add result if present (may be None if SKIP strategy was used)
    if "result" in data and data["result"] is not None:
        result_value = data["result"]
        if not isinstance(result_value, str):
            result_value = json.dumps(result_value)
        properties.append(KGProperty(key=SysProperties.RESULT, value=result_value))
    
    # Add custom data (e.g., from Pydantic models)
    if "data" in data:
        properties.append(KGProperty(key="http://kgcore.org/system/data", value=json.dumps(data["data"])))

    # Instance handling: create or update deterministic instance entity
    instance_id = data.get("instance_id")
    instance_props: list[KGProperty] = []
    if instance_id and class_id:
        instance_props.append(KGProperty(key=SysProperties.INSTANCE_ID, value=instance_id))
        # Serialize attributes if present
        if "attributes" in data:
            try:
                instance_props.append(
                    KGProperty(
                        key="http://kgcore.org/system/attributes",
                        value=json.dumps(data["attributes"]),
                    )
                )
            except Exception:
                pass
    
    # Add any additional metadata
    for key, value in data.items():
        if key not in ("event", "class", "function", "model", "module", "args", "kwargs", "result", "data"):
            if not isinstance(value, str):
                value = json.dumps(value)
            properties.append(KGProperty(key=f"http://kgcore.org/system/{key}", value=value))
    
    try:
        # Create instance entity if provided
        if instance_id and class_id:
            try:
                kg.create_entity(
                    id=instance_id,
                    types=[SysLabels.Instance, SysLabels.Object],
                    properties=instance_props,
                )
                kg.create_relation(
                    source=instance_id,
                    target=class_id,
                    type=SysLabels.IS_INSTANCE_OF,
                )
            except Exception:
                pass

        # Create run entity
        kg.create_entity(
            id=run_id,
            types=[SysLabels.Run],
            properties=properties,
        )
        
        # Create CALLS relation if we have a function/class ID
        if func_id:
            try:
                kg.create_relation(
                    source=run_id,
                    target=func_id,
                    type=SysLabels.CALLS,
                )
            except Exception:
                # Relation creation might fail if function/class not registered yet
                pass

        # Link run to instance if available
        if instance_id:
            try:
                kg.create_relation(
                    source=run_id,
                    target=instance_id,
                    type=SysLabels.CALLS,
                )
            except Exception:
                pass
    except Exception:
        # Silently fail if KG is not available
        pass


def _get_kg() -> Optional[KnowledgeGraph]:
    """
    Internal function to get the current KnowledgeGraph.
    
    Returns:
        The current KnowledgeGraph instance, or None if not available
    """
    return _default_kg
