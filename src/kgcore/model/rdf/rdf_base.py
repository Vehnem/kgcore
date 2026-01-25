from __future__ import annotations

from typing import Optional, Iterable, Any, Dict, List, TYPE_CHECKING
import rdflib
from rdflib import Graph, URIRef, Literal, RDF
from rdflib.namespace import RDF as RDF_NS

from kgcore.api.backend import KGBackend
from kgcore.api.model import KGModel
from kgcore.api.kg import KGEntity, KGRelation, KGProperty
from kgcore.backend.rdf.rdf_rdflib import RDFBackend

if TYPE_CHECKING:
    from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend

class RDFBaseModel(KGModel):
    """
    Very minimal RDF model:
      - entities are IRIs
      - rdf:type for types
      - properties are predicate–literal triples
      - relations are predicate–IRI triples
      - annotations are ignored (handled in RDFReification/RDFStar variants)
    """

    family = "rdf"

    @property
    def name(self) -> str:
        return "rdf-base"

    # --- helpers ---

    def _iri(self, value: str) -> URIRef:
        # For the sketch, assume `value` is already a full IRI string.
        return URIRef(value)

    # --- entity ops ---

    def create_entity(
        self,
        backend: KGBackend,
        id: Optional[str] = None,
        types: Optional[Iterable[str]] = None,
        properties: Optional[List[KGProperty] | Dict[str, Any]] = None,
    ) -> KGEntity:
        assert isinstance(backend, RDFBackend), "RDFBaseModel requires RDFBackend"

        if id is None:
            # In a real library, you'd generate a fresh IRI or blank node.
            raise ValueError("RDFBaseModel.create_entity requires an explicit IRI for now")

        s = self._iri(id)
        triples: list[tuple[rdflib.term.Node, rdflib.term.Node, rdflib.term.Node]] = []

        # Types
        for t in (types or []):
            triples.append((s, RDF.type, self._iri(t)))

        # Properties - handle both List[KGProperty] and Dict[str, Any]
        if properties is not None:
            if isinstance(properties, list):
                # List of KGProperty objects
                for prop in properties:
                    p = self._iri(prop.key)
                    o = Literal(prop.value) if not isinstance(prop.value, Literal) else prop.value
                    triples.append((s, p, o))
            else:
                # Dict[str, Any]
                for prop_iri_str, value in properties.items():
                    p = self._iri(prop_iri_str)
                    o = Literal(value) if not isinstance(value, Literal) else value
                    triples.append((s, p, o))

        backend.insert_triples(triples)
        
        # Convert properties to KGProperty list
        prop_list: List[KGProperty] = []
        if properties is not None:
            if isinstance(properties, list):
                prop_list = properties
            else:
                prop_list = [KGProperty(key=k, value=v) for k, v in properties.items()]
        
        return KGEntity(id=id, labels=list(types or []), properties=prop_list)

    def get_entity(
        self,
        backend: KGBackend,
        id: str,
    ) -> Optional[Dict[str, Any]]:
        assert isinstance(backend, RDFBackend), "RDFBaseModel requires RDFBackend"

        s_iri = self._iri(id)

        # 1) get types
        # Escape the IRI properly for SPARQL
        s_iri_str = str(s_iri)
        types_query = f"""
        SELECT ?type WHERE {{
          <{s_iri_str}> a ?type .
        }}
        """
        types_result = backend.query_sparql(types_query)
        types = [str(row["type"]) for row in types_result]

        # 2) get properties (exclude rdf:type)
        props_query = f"""
        SELECT ?p ?o WHERE {{
          <{s_iri_str}> ?p ?o .
          FILTER (?p != <{RDF.type}>)
        }}
        """
        props_result = backend.query_sparql(props_query)

        properties: Dict[str, Any] = {}
        for row in props_result:
            p = str(row["p"])
            o = row["o"]
            # Very naive: if it's a Literal, take its Python value, else its string IRI
            if isinstance(o, Literal):
                value = o.toPython()
            else:
                value = str(o)
            properties[p] = value

        if not types and not properties:
            # nothing found at all: treat as missing entity
            return None

        return {
            "id": id,
            "types": types,
            "properties": properties,
        }

    def update_entity(
        self,
        backend: KGBackend,
        entity: KGEntity,
    ) -> None:
        assert isinstance(backend, RDFBackend), "RDFBaseModel requires RDFBackend"

        s_iri = self._iri(entity.id)
        
        # First, delete all existing triples for this entity
        delete_query = f"""
        DELETE WHERE {{
          <{s_iri}> ?p ?o .
        }}
        """
        # Use the backend's graph directly if it's an RDFLibBackend
        if hasattr(backend, 'graph'):
            backend.graph.update(delete_query)
        
        # Now insert new triples
        triples: list[tuple[rdflib.term.Node, rdflib.term.Node, rdflib.term.Node]] = []

        # Types
        for t in entity.labels:
            triples.append((s_iri, RDF.type, self._iri(t)))

        # Properties - convert values to Literals
        for prop in entity.properties:
            p = self._iri(prop.key)
            # Convert value to Literal if it's not already a Literal
            if isinstance(prop.value, Literal):
                o = prop.value
            else:
                o = Literal(prop.value)
            triples.append((s_iri, p, o))

        backend.insert_triples(triples)

    def delete_entity(
        self,
        backend: KGBackend,
        id: str,
    ) -> None:
        assert isinstance(backend, RDFBackend), "RDFBaseModel requires RDFBackend"

        s_iri = self._iri(id)
        s_iri_str = str(s_iri)
        # SPARQL 1.1 DELETE WHERE
        delete_query = f"""
        DELETE WHERE {{
          <{s_iri_str}> ?p ?o .
        }};
        """
        # rdflib's Graph.update supports SPARQL UPDATE. We'll go direct to graph here
        # by using the backend's graph, or in a more "pure" interface we'd add an `update_sparql`.
        if hasattr(backend, 'graph'):
            backend.graph.update(delete_query)
        else:
            # In a more complete design, RDFBackend would have `update_sparql`,
            # and we'd call backend.update_sparql(delete_query) here.
            raise NotImplementedError("delete_entity only implemented for RDFLibBackend in this sketch")

    # --- relation ops ---

    def create_relation(
        self,
        backend: KGBackend,
        subject: str,
        predicate: str,
        object: str,
        annotations: Optional[Dict[str, Any]] = None,
    ) -> KGRelation:
        assert isinstance(backend, RDFBackend), "RDFBaseModel requires RDFBackend"

        s = self._iri(subject)
        p = self._iri(predicate)
        o = self._iri(object)

        triple = (s, p, o)
        backend.insert_triples([triple])

        # RDF base model ignores annotations; RDFReification/RDFStar would override this.
        properties = [KGProperty(key=k, value=v) for k, v in (annotations or {}).items()]
        return KGRelation(
            id=f"{subject}-{predicate}-{object}",  # Simple ID generation
            type=predicate,
            source=subject,
            target=object,
            properties=properties,
        )

    def get_neighbors(
        self,
        backend: KGBackend,
        entity_id: str,
        predicate: Optional[str] = None,
    ) -> List[KGEntity]:
        """Get neighboring entities connected via relations."""
        assert isinstance(backend, RDFBackend), "RDFBaseModel requires RDFBackend"
        
        s_iri = self._iri(entity_id)
        
        if predicate:
            # Query for specific predicate
            query = f"""
            SELECT ?o WHERE {{
              <{s_iri}> <{self._iri(predicate)}> ?o .
              FILTER (isIRI(?o))
            }}
            """
        else:
            # Query for all neighbors
            query = f"""
            SELECT DISTINCT ?o WHERE {{
              <{s_iri}> ?p ?o .
              FILTER (isIRI(?o))
            }}
            """
        
        result = backend.query_sparql(query)
        neighbors: List[KGEntity] = []
        
        for row in result:
            o = row["o"]
            if isinstance(o, URIRef):
                # Get entity data for the neighbor
                neighbor_data = self.get_entity(backend, str(o))
                if neighbor_data:
                    properties = [KGProperty(key=k, value=v) for k, v in neighbor_data.get("properties", {}).items()]
                    neighbors.append(KGEntity(
                        id=neighbor_data["id"],
                        labels=neighbor_data.get("types", []),
                        properties=properties,
                    ))
                else:
                    # If we can't get full data, create minimal entity
                    neighbors.append(KGEntity(id=str(o)))
        
        return neighbors


    def triples(self, backend: RDFBackend, s, p, o) -> List[tuple[rdflib.term.Node, rdflib.term.Node, rdflib.term.Node]]:
        """Get all triples matching the given subject, predicate, and object."""
        return backend.list_triples(s, p, o)