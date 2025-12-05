"""Backend implementations for kgcore."""

from .factory import create_backend, register_backend, get_available_backends, BackendFactory
from .core.core_memory import InMemoryBackend
from .rdf.rdf_rdflib import RDFBackend, RDFLibBackend

__all__ = [
    "create_backend",
    "register_backend", 
    "get_available_backends",
    "BackendFactory",
    "InMemoryBackend",
    "RDFBackend",
    "RDFLibBackend",
]

