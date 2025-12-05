from typing import Iterable, Optional, List
from rdflib import term
from kgcore.api.backend import KGBackend
from abc import abstractmethod
import rdflib

class RDFBackend(KGBackend):
    """
    RDF-specific backend interface, using triples and SPARQL.
    """

    supported_model_families = ["rdf"]

    @abstractmethod
    def insert_triples(self, triples: Iterable[tuple[rdflib.term.Node,
                                                     rdflib.term.Node,
                                                     rdflib.term.Node]]) -> None:
        ...

    @abstractmethod
    def delete_triples(self, triples: Iterable[tuple[rdflib.term.Node,
                                                     rdflib.term.Node,
                                                     rdflib.term.Node]]) -> None:
        ...

    def list_triples(self, s, p, o) -> List[tuple[rdflib.term.Node, rdflib.term.Node, rdflib.term.Node]]:
        return self.graph.triples((s, p, o))

    @abstractmethod
    def query_sparql(self, query: str):
        ...
