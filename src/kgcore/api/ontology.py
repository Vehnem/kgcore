# TODO not in use yet
from dataclasses import dataclass, field
from typing import List, Self, Dict
from enum import Enum
from rdflib import Graph, RDF, OWL, RDFS, SKOS, URIRef
from pathlib import Path
# A util for ontology related tasks

# Common namespaces
RDF_NAMESPACE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NAMESPACE = "http://www.w3.org/2000/01/rdf-schema#"
OWL_NAMESPACE = "http://www.w3.org/2002/07/owl#"
XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema#"
PROV_NAMESPACE = "http://www.w3.org/ns/prov#"
DCTERMS_NAMESPACE = "http://purl.org/dc/terms/"
SCHEMA_NAMESPACE = "http://schema.org/"
DUBLIN_CORE_NAMESPACE = "http://purl.org/dc/elements/1.1/"


class OntologyExtractor:
    """
    A class to extract the ontology from a given rdfgraph
    all entities of type owl:Class, owl:ObjectProperty, owl:DatatypeProperty, owl:AnnotationProperty, owl:NamedIndividual
    """
    pass

@dataclass
class OwlClass:
    uri: str
    label: str
    alias: List[str]
    description: str
    superclasses: List[Self]
    subclases: List[Self]
    equivalent: set[str]
    disjointWith: set[str]

    def __str__(self) -> str:
        return f"OwlClass(\nuri={self.uri},\nlabel={self.label},\nalias={self.alias},\nsuperclasses={self.superclasses},\nsubclases={self.subclases},\nequivalent={self.equivalent})"


class OwlPropertyType(Enum):
    ObjectProperty = "ObjectProperty"
    DatatypeProperty = "DatatypeProperty"
    AnnotationProperty = "AnnotationProperty"


@dataclass
class OwlProperty:
    uri: str
    type: OwlPropertyType
    label: str
    alias: List[str]
    description: str
    domain: OwlClass
    range: OwlClass
    equivalent: set[str]
    min_cardinality: int = 1
    max_cardinality: int = 10000


    def __str__(self) -> str:
        return f"OwlProperty(\nuri={self.uri},\ntype={self.type},\nlabel={self.label},\nalias={self.alias},\ndomain={self.domain},\nrange={self.range},\nequivalent={self.equivalent})"

@dataclass
class Ontology:
    # uri: str TODO
    classes: List[OwlClass] = field(default_factory=list)
    properties: List[OwlProperty] = field(default_factory=list)

    def check_equivalent(self, uri_1: str, uri_2: str):

        for _class in self.classes:
            if uri_1 in _class.equivalent or uri_2 in _class.equivalent:
                return True

        for property in self.properties:
            if uri_1 in property.equivalent or uri_2 in property.equivalent:
                return True

        return False

    def get_domain_range(self, uri: str):
        for property in self.properties:
            if uri == property.uri:
                domain = property.domain.uri if property.domain else None
                range = property.range.uri if property.range else None
                return domain, range
        return None, None
    
    def add_class(self, uri: str, label: str = None, parents: List[str] = None):
        """Add a class to the ontology."""
        if label is None:
            label = uri
        if parents is None:
            parents = []
        
        # Check if class already exists
        for cls in self.classes:
            if cls.uri == uri:
                # Update existing class
                cls.label = label
                cls.superclasses = [self._get_class_by_uri(p) for p in parents if self._get_class_by_uri(p) is not None]
                return
        
        # Create new class
        superclasses = [self._get_class_by_uri(p) for p in parents if self._get_class_by_uri(p) is not None]
        new_class = OwlClass(
            uri=uri,
            label=label,
            alias=[],
            description="",
            superclasses=superclasses,
            subclases=[],
            equivalent=set(),
            disjointWith=set()
        )
        self.classes.append(new_class)
        
        # Update parent-child relationships
        for parent_uri in parents:
            parent_class = self._get_class_by_uri(parent_uri)
            if parent_class is not None and new_class not in parent_class.subclases:
                parent_class.subclases.append(new_class)
    
    def add_predicate(self, uri: str, label: str = None, domain: List[str] = None, range: List[str] = None):
        """Add a predicate/property to the ontology."""
        if label is None:
            label = uri
        if domain is None:
            domain = []
        if range is None:
            range = []
        
        # Check if property already exists
        for prop in self.properties:
            if prop.uri == uri:
                # Update existing property
                prop.label = label
                if domain:
                    prop.domain = self._get_class_by_uri(domain[0]) if domain else None
                if range:
                    prop.range = self._get_class_by_uri(range[0]) if range else None
                return
        
        # Create new property (default to ObjectProperty)
        domain_class = self._get_class_by_uri(domain[0]) if domain else None
        range_class = self._get_class_by_uri(range[0]) if range else None
        
        new_property = OwlProperty(
            uri=uri,
            type=OwlPropertyType.ObjectProperty,
            label=label,
            alias=[],
            description="",
            domain=domain_class,
            range=range_class,
            equivalent=set(),
            min_cardinality=1,
            max_cardinality=10000
        )
        self.properties.append(new_property)
    
    def validate_triple(self, subject: str, predicate: str, object: str) -> tuple[bool, str]:
        """Validate if a triple is allowed by the ontology."""
        # Get domain and range for the predicate
        domain, range = self.get_domain_range(predicate)
        
        if domain is None and range is None:
            # No constraints, allow it
            return True, "No constraints on predicate"
        
        # Check if subject is in domain (or a subclass)
        if domain is not None:
            subject_class = self._get_class_by_uri(subject)
            if subject_class is None:
                # Subject is not a class, check if it's an instance
                # For now, if domain is specified, subject should match or be subclass
                # This is simplified - in reality we'd need instance checking
                return False, f"Subject {subject} does not match domain {domain}"
            
            # Check if subject class is domain or subclass of domain
            domain_class = self._get_class_by_uri(domain)
            if domain_class is None:
                return False, f"Domain class {domain} not found in ontology"
            
            if not self._is_subclass_or_equal(subject_class, domain_class):
                return False, f"Subject class {subject} is not a subclass of domain {domain}"
        
        # Check if object is in range (or a subclass)
        if range is not None:
            object_class = self._get_class_by_uri(object)
            if object_class is None:
                # Object is not a class, check if it's an instance
                return False, f"Object {object} does not match range {range}"
            
            # Check if object class is range or subclass of range
            range_class = self._get_class_by_uri(range)
            if range_class is None:
                return False, f"Range class {range} not found in ontology"
            
            if not self._is_subclass_or_equal(object_class, range_class):
                return False, f"Object class {object} is not a subclass of range {range}"
        
        return True, "Triple is valid"
    
    def _get_class_by_uri(self, uri: str) -> OwlClass | None:
        """Get a class by its URI."""
        for cls in self.classes:
            if cls.uri == uri:
                return cls
        return None
    
    def _is_subclass_or_equal(self, child: OwlClass, parent: OwlClass) -> bool:
        """Check if child is a subclass of parent (or equal)."""
        if child.uri == parent.uri:
            return True
        
        # Check direct superclasses
        for superclass in child.superclasses:
            if superclass.uri == parent.uri:
                return True
            # Recursively check superclasses
            if self._is_subclass_or_equal(superclass, parent):
                return True
        
        return False

    def __str__(self) -> str:
        # INSERT_YOUR_CODE
        import json
        def default(obj):
            # Handle dataclasses and enums
            if hasattr(obj, "__dataclass_fields__"):
                return {k: v for k, v in obj.__dict__.items()}
            if isinstance(obj, set):
                return list(obj)
            if isinstance(obj, Enum):
                return obj.value
            return str(obj)
        return json.dumps(self, default=default, indent=2)

from rdflib import URIRef, Graph
from rdflib.query import ResultRow
from rdflib.namespace import OWL

def get_property_cardinality(ontology_graph: Graph, property: str):
    # if functional property
    property_type_rs = ontology_graph.query(
        """
        SELECT ?type
        WHERE {
            ?property a ?type .
        }
        """,
        initBindings={"property": URIRef(property)}
    )

    property_types = set(str(row["type"]) for row in property_type_rs if isinstance(row, ResultRow))
    
    if str(OWL.FunctionalProperty) in property_types:
        return (0, 1)
    
    # if restriction on property
    #_:restriction a owl:Restriction ;
    # owl:onProperty ex:hasSSN ;
    # owl:maxCardinality "1"^^xsd:nonNegativeInteger .

    restriction_rs = ontology_graph.query(
        """
        SELECT ?maxCardinality ?minCardinality
        WHERE {
            ?restriction a owl:Restriction ;
            owl:onProperty ?property ;
            OPTIONAL { ?restriction owl:maxCardinality ?maxCardinality . }
            OPTIONAL { ?restriction owl:minCardinality ?minCardinality . }
        }
        """,
        initBindings={"property": URIRef(property)}
    )

    max_cardinality = 10000
    min_cardinality = 1
    for row in restriction_rs:
        if isinstance(row, ResultRow):
            if row["maxCardinality"] is not None:
                max_cardinality = int(row["maxCardinality"])
            if row["minCardinality"] is not None:
                min_cardinality = int(row["minCardinality"])
        

    return (min_cardinality, max_cardinality)

class OntologyUtil:

    def __init__(self):
        pass

    @staticmethod
    def extract_ontology(ontology_file):
        pass

    @staticmethod
    def load_ontology_from_file(ontology_file: Path):
        graph = Graph()
        graph.parse(ontology_file)
        return OntologyUtil.load_ontology_from_graph(graph)


    @staticmethod
    def load_ontology_from_graph(graph):

        classes : Dict[str, OwlClass] = {}
        properties : Dict[str, OwlProperty] = {}

        def fetch_info(uri: str):
            label = str(graph.value(s, RDFS.label))
            if not label: label = str(s)

            description = str(graph.value(s, RDFS.comment))
            if not description: description = ""

            alias = [ str(o) for s, p, o in graph.triples((uri, SKOS.altLabel, None)) ]
            if not alias: alias = []

            equivalent = set() 
            for _, _, o in graph.triples((uri, OWL.equivalentClass, None)):
                equivalent.add(str(o))
            for _, _, o in graph.triples((uri, OWL.equivalentProperty, None)):
                equivalent.add(str(o))

            return label, alias, equivalent, description

        def fetch_property_info(uri: URIRef):
            label, alias, equivalent, description = fetch_info(uri)

            domain = None
            domain_uri = graph.value(uri, RDFS.domain)
            if domain_uri and str(domain_uri) in classes:
                domain = classes[str(domain_uri)]

            range = None
            range_uri = graph.value(uri, RDFS.range)
            if range_uri:
                range_uri_str = str(range_uri)
                if range_uri_str in classes:
                    range = classes[range_uri_str]
                elif range_uri_str.startswith(XSD_NAMESPACE):
                    range = OwlClass(
                        uri=range_uri_str,
                        label=range_uri_str,
                        alias=[],
                        superclasses=[],
                        subclases=[],
                        equivalent=set(),
                        description="",
                        disjointWith=set()
                    )

            min_cardinality, max_cardinality = get_property_cardinality(graph, uri)

            return label, alias, equivalent, description, domain, range, min_cardinality, max_cardinality

        def fetch_class_info(uri: URIRef):

            label, alias, equivalent, description = fetch_info(uri)

            disjointWith = set()
            for _, _, o in graph.triples((uri, OWL.disjointWith, None)):
                disjointWith.add(str(o))

            for s, _, _ in graph.triples((None, OWL.disjointWith, uri)):
                disjointWith.add(str(s))

            return label, alias, equivalent, description, disjointWith

        for s, p, o in graph.triples((None, RDF.type, OWL.Class)):

            label, alias, equivalent, description, disjointWith = fetch_class_info(s)

            classes[str(s)] = OwlClass(uri=str(s), label=label, alias=alias, superclasses=[], subclases=[], equivalent=equivalent, description=description, disjointWith=disjointWith)

        for s, p, o in graph.triples((None, RDF.type, OWL.ObjectProperty)):
            label, alias, equivalent, description, domain, range, min_cardinality, max_cardinality = fetch_property_info(s)
            properties[str(s)] = OwlProperty(uri=str(s), type=OwlPropertyType.ObjectProperty, label=label, alias=alias, domain=domain, range=range, equivalent=equivalent, description=description, min_cardinality=min_cardinality, max_cardinality=max_cardinality)

        for s, p, o in graph.triples((None, RDF.type, OWL.DatatypeProperty)):
            label, alias, equivalent, description, domain, range, min_cardinality, max_cardinality = fetch_property_info(s)
            properties[str(s)] = OwlProperty(uri=str(s), type=OwlPropertyType.DatatypeProperty, label=label, alias=alias, domain=domain, range=range, equivalent=equivalent, description=description, min_cardinality=min_cardinality, max_cardinality=max_cardinality)


        return Ontology(classes=list(classes.values()), properties=list(properties.values()))

if __name__ == "__main__":
    ontology_util = OntologyUtil()
    ontology = ontology_util.load_ontology_from_file("/home/marvin/project/data/current/ontology.ttl")
    print(ontology)