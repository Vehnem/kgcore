"""RDFLib-based RDF backend implementation."""

from __future__ import annotations

from typing import Iterable, Optional, List
from rdflib import term
from kgcore.api.backend import KGBackend
from abc import abstractmethod
import rdflib

from kgcore.backend.rdf.rdfbackend import RDFBackend

class RDFLibBackend(RDFBackend):
    """
    Minimal rdflib-based RDF backend (in-memory Graph).
    """

    def __init__(self, graph: Optional[rdflib.Graph] = None):
        self.graph = graph or rdflib.Graph()

    def get_rdflibgraph(self):
        return self.graph

    @property
    def name(self) -> str:
        return "rdflib"

    def connect(self) -> None:
        # For in-memory rdflib, nothing to do
        pass

    def close(self) -> None:
        # Could serialize or free resources here if needed
        pass

    def insert_triples(self, triples):
        for s, p, o in triples:
            self.graph.add((s, p, o))

    def delete_triples(self, triples):
        for s, p, o in triples:
            self.graph.remove((s, p, o))

    def query_sparql(self, query: str):
        return self.graph.query(query)
