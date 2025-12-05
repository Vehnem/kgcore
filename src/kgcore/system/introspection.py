"""
Generic fallback extraction for non-annotatable objects.

This module provides introspection functions that extract KG metadata
from plain Python classes and functions when they don't implement KGAnnotatable.
"""

from typing import Mapping, Any, Callable
import inspect


def default_class_definition(cls: type) -> Mapping[str, Any]:
    """
    Extract KG definition metadata from a plain Python class.
    
    Args:
        cls: The class to introspect
        
    Returns:
        Dictionary containing class metadata (kind, name, module, doc, etc.)
    """
    return {
        "kind": "class",
        "name": cls.__name__,
        "module": cls.__module__,
        "doc": cls.__doc__,
        "bases": [base.__name__ for base in cls.__bases__ if base is not object],
    }


def default_function_definition(fn: Callable) -> Mapping[str, Any]:
    """
    Extract KG definition metadata from a plain Python function.
    
    Args:
        fn: The function to introspect
        
    Returns:
        Dictionary containing function metadata (kind, name, module, doc, signature)
    """
    return {
        "kind": "function",
        "name": fn.__name__,
        "module": fn.__module__,
        "doc": fn.__doc__,
        "signature": str(inspect.signature(fn)),
    }


def default_class_call(obj: Any, *args: Any, **kwargs: Any) -> Mapping[str, Any]:
    """
    Extract KG call metadata from a class instantiation.
    
    Args:
        obj: The instance that was just created
        *args: Positional arguments passed to __init__
        **kwargs: Keyword arguments passed to __init__
        
    Returns:
        Dictionary containing call event metadata
    """
    return {
        "event": "class_init",
        "class": type(obj).__name__,
        "module": type(obj).__module__,
        "args": args,
        "kwargs": kwargs,
    }


def default_function_call(
    fn: Callable, *args: Any, result: Any = None, **kwargs: Any
) -> Mapping[str, Any]:
    """
    Extract KG call metadata from a function call.
    
    Args:
        fn: The function that was called
        *args: Positional arguments passed to the function
        **kwargs: Keyword arguments passed to the function
        result: The return value of the function call (optional)
        
    Returns:
        Dictionary containing call event metadata
    """
    return {
        "event": "function_call",
        "function": fn.__name__,
        "module": fn.__module__,
        "args": args,
        "kwargs": kwargs,
        "result": result,
    }


def is_annotatable(obj: Any) -> bool:
    """
    Check if an object implements the KGAnnotatable protocol.
    
    Args:
        obj: The object to check
        
    Returns:
        True if the object has both kg_definition and kg_call methods
    """
    return hasattr(obj, "kg_definition") and hasattr(obj, "kg_call")


def is_class(obj: Any) -> bool:
    """
    Check if an object is a class (type).
    
    Args:
        obj: The object to check
        
    Returns:
        True if the object is a class
    """
    return isinstance(obj, type)


def is_function(obj: Any) -> bool:
    """
    Check if an object is a function (but not a class).
    
    Args:
        obj: The object to check
        
    Returns:
        True if the object is callable but not a class
    """
    return callable(obj) and not isinstance(obj, type)
