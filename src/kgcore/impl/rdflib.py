from rdflib import Graph, URIRef, Literal
from kgcore.model.graph import Triple, Node, Literal as LiteralModel

class RDFLibGraph(Graph):
    def __init__(self):
        super().__init__()

    def add_triple(self, triple: Triple):
        self.add((triple.subject.uri, triple.predicate.uri, triple.object.uri))

    def get_triples(self):
        return [Triple(Node(str(s)), Node(str(p)), Node(str(o))) for s, p, o in self]