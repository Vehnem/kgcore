"""RDF backends for kgcore."""

from .rdf_rdflib import RDFBackend, RDFLibBackend

__all__ = [
    "RDFBackend",
    "RDFLibBackend",
]
