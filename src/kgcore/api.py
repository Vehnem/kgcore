# kgcore/api.py
from __future__ import annotations
from typing import Literal, Optional
from kgcore.backend.memory import InMemoryGraph
from kgcore.backend.rdf_file import RDFFileGraph
from kgcore.model.base import KGGraph

BackendName = Literal["memory", "rdf_file"]  # extend later

def KG(backend: BackendName = "memory", **kwargs) -> KGGraph:
    if backend == "memory":
        return InMemoryGraph()
    elif backend == "rdf_file":
        file_path = kwargs.get("file_path", "kg.rdf")
        base_iri = kwargs.get("base_iri", "http://example.org/")
        format = kwargs.get("format", "turtle")
        return RDFFileGraph(file_path, base_iri, format)
    raise ValueError(f"Unknown backend: {backend}")
