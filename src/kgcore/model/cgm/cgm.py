"""
Core Graph Model (CGM) - An Intermediate Representation for Knowledge Graphs

This module provides a minimal, precise intermediate representation (IR) for knowledge graphs
that serves as a bridge between different graph models (RDF, Property Graphs, etc.).

**Purpose**: This is a research and teaching library, not a high-performance production system.
The goal is to:
- Make differences between graph models explicit and observable
- Provide multiple conversion strategies ("modes")
- Enable inspection of what gets lost/preserved in each conversion mode
- Support round-trip conversions for teaching and research

The CoreGraph IR is designed to be:
- Simple enough to explain on a whiteboard
- Structured enough to express common patterns
- Stable enough to support multiple adapters

Think of it as "the IR for a graph compiler" that enables experimentation with
graph representations and makes information loss and design tradeoffs explicit.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Hashable, Optional, TypeVar, Generic, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from kgcore.api.query import QueryResult


# Type aliases
CoreId = Hashable
"""A unique identifier for any core graph element (node, edge, or literal)."""


@dataclass
class CoreLiteral:
    """
    Represents a typed literal value in the core graph model.
    
    Attributes:
        value: The literal value as a string
        datatype: Optional datatype URI (e.g., "http://www.w3.org/2001/XMLSchema#string")
        language: Optional language tag (e.g., "en", "de")
    """
    value: str
    datatype: Optional[str] = None
    language: Optional[str] = None
    
    def __hash__(self) -> int:
        """Make CoreLiteral hashable for use in sets/dicts."""
        return hash((self.value, self.datatype, self.language))


@dataclass
class CoreNode:
    """
    Represents a node in the core graph model.
    
    Attributes:
        id: Unique identifier for the node
        labels: List of labels/types for the node (e.g., ["Person", "Agent"])
        properties: Dictionary of property-value pairs
    """
    id: CoreId
    labels: List[str] = field(default_factory=list)
    properties: Dict[str, Any | CoreLiteral] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        """Make CoreNode hashable based on its ID."""
        return hash(self.id)


@dataclass
class CoreEdge:
    """
    Represents an edge (relationship) in the core graph model.
    
    Attributes:
        id: Unique identifier for the edge (enables edge identity and properties)
        source: ID of the source node
        target: ID of the target node
        label: The edge label/type (e.g., "knows", "locatedIn")
        properties: Dictionary of property-value pairs on the edge
    """
    id: CoreId
    source: CoreId
    target: CoreId
    label: str
    properties: Dict[str, Any | CoreLiteral] = field(default_factory=dict)
    
    def __hash__(self) -> int:
        """Make CoreEdge hashable based on its ID."""
        return hash(self.id)


@dataclass
class CoreGraph:
    """
    The core graph model - a collection of nodes and edges with metadata.
    
    This is the intermediate representation that serves as a bridge between
    different graph models (RDF, Property Graphs, etc.).
    
    Attributes:
        nodes: Dictionary mapping node IDs to CoreNode instances
        edges: Dictionary mapping edge IDs to CoreEdge instances
        metadata: Dictionary for graph-level metadata (e.g., provenance, mode info)
    """
    nodes: Dict[CoreId, CoreNode] = field(default_factory=dict)
    edges: Dict[CoreId, CoreEdge] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_node(self, node: CoreNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
    
    def add_edge(self, edge: CoreEdge) -> None:
        """Add an edge to the graph."""
        self.edges[edge.id] = edge
    
    def get_node(self, node_id: CoreId) -> Optional[CoreNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: CoreId) -> Optional[CoreEdge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)


# Type variable for backend-specific graph types
T = TypeVar('T')


class ConversionMode(Enum):
    """Enumeration of conversion modes (can be extended per backend)."""
    SIMPLE = "simple"
    DEFAULT = "default"


@dataclass
class ConversionResult:
    """
    Result of a conversion operation, including warnings and metadata.
    
    This is useful for teaching/research to understand what information
    is preserved or lost during conversion.
    
    Attributes:
        graph: The converted graph
        warnings: List of warning messages about information loss or approximations
        mode: The conversion mode used
        metadata: Additional metadata about the conversion
    """
    graph: CoreGraph | T
    warnings: List[str] = field(default_factory=list)
    mode: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)


class GraphBackend(ABC, Generic[T]):
    """
    Abstract base class for graph backend adapters.
    
    Each backend (RDF, Property Graph, etc.) implements this interface
    to provide bidirectional conversion to/from the CoreGraph IR and query capabilities.
    """

    @abstractmethod
    def to_core(self, graph: T, mode: str = "default") -> ConversionResult:
        """
        Convert a backend-specific graph to CoreGraph.
        
        Args:
            graph: The backend-specific graph to convert
            mode: Conversion mode (e.g., "simple", "reified_edges", "quads_with_context")
        
        Returns:
            ConversionResult containing the CoreGraph and any warnings
        """
        pass

    @abstractmethod
    def from_core(self, core: CoreGraph, mode: str = "default") -> ConversionResult:
        """
        Convert a CoreGraph to a backend-specific graph.
        
        Args:
            core: The CoreGraph to convert
            mode: Conversion mode (e.g., "edge_properties_as_reification")
        
        Returns:
            ConversionResult containing the backend-specific graph and any warnings
        """
        pass
    
    def query(self, query_string: str, query_type: str = None) -> "QueryResult":
        """
        Execute a query on the backend's graph.
        
        Args:
            query_string: The query string in the backend's native query language
            query_type: Optional query type hint (e.g., "sparql", "cypher")
        
        Returns:
            QueryResult containing the query results
        
        Raises:
            NotImplementedError: If querying is not supported by this backend
        """
        raise NotImplementedError(f"Querying not supported by {self.__class__.__name__}")
    
    def get_available_modes(self) -> Dict[str, str]:
        """
        Get available conversion modes for this backend.
        
        Returns:
            Dictionary mapping mode names to descriptions
        """
        return {}
    
    def get_supported_query_types(self) -> List[str]:
        """
        Get list of supported query types for this backend.
        
        Returns:
            List of query type names (e.g., ["sparql"], ["cypher"], etc.)
        """
        return []


class RDFBackend(GraphBackend):
    """
    Adapter for RDF graphs (using rdflib).
    
    Provides multiple conversion modes to explore different ways of
    mapping RDF concepts to/from the CoreGraph IR.
    
    Can work with either an RDFStore (for persistent storage) or an rdflib.Graph
    directly (for in-memory conversions).
    """
    
    def __init__(self, store=None):
        """
        Initialize the RDF backend adapter.
        
        Args:
            store: Optional RDFStore instance for persistent storage.
                  If None, conversions work with rdflib.Graph objects directly.
        """
        from kgcore.api.rdf_store import RDFStore
        self._store = store
        if store is not None and not isinstance(store, RDFStore):
            raise TypeError(f"Expected RDFStore, got {type(store)}")
        
        self._modes = {
            "simple": (
                "Each RDF triple becomes one CoreEdge. "
                "No named graphs, no reification, no RDF*. "
                "rdf:type becomes a node label."
            ),
            "reified_edges": (
                "RDF reification gets turned into explicit edge nodes with properties. "
                "Reified statements become CoreNodes connected to the original edge."
            ),
            "quads_with_context": (
                "Named graphs or graph names become graph-level properties or edge properties. "
                "Quad context is preserved in edge properties."
            ),
        }
    
    def to_core(self, graph=None, mode: str = "simple") -> ConversionResult:
        """
        Convert an RDF graph to CoreGraph.
        
        Args:
            graph: Optional rdflib.Graph instance. If None and a store is configured,
                   uses the store. If None and no store, raises ValueError.
            mode: Conversion mode ("simple", "reified_edges", "quads_with_context")
        
        Returns:
            ConversionResult with CoreGraph and warnings
        """
        from rdflib import Graph, RDF, URIRef, Literal, BNode
        from kgcore.api.rdf_store import RDFStore
        
        # Determine source: use store if available and no graph provided, otherwise use graph
        if graph is None:
            if self._store is None:
                raise ValueError("Either provide a graph or initialize RDFBackend with a store")
            # Use store - iterate over all triples
            rdf_source = self._store
        else:
            # Use provided graph
            if not isinstance(graph, Graph):
                raise TypeError(f"Expected rdflib.Graph, got {type(graph)}")
            rdf_source = graph
        
        if mode not in self._modes:
            raise ValueError(f"Unknown mode: {mode}. Available: {list(self._modes.keys())}")
        
        core = CoreGraph()
        warnings = []
        node_map: Dict[Any, CoreId] = {}
        
        # Track RDF types for labels
        rdf_types: Dict[CoreId, List[str]] = {}
        
        if mode == "simple":
            # Simple mode: each triple becomes an edge
            # Get triples from either store or graph
            if isinstance(rdf_source, RDFStore):
                triples = rdf_source.triples((None, None, None))
            else:
                # For rdflib.Graph, iterate over triples
                triples = rdf_source.triples((None, None, None))
            
            for s, p, o in triples:
                # Convert subject to node
                if s not in node_map:
                    node_id = self._rdf_term_to_id(s)
                    node_map[s] = node_id
                    core.add_node(CoreNode(id=node_id, labels=[], properties={}))
                
                # Convert object to node (if it's not a literal)
                if isinstance(o, (URIRef, BNode)):
                    if o not in node_map:
                        node_id = self._rdf_term_to_id(o)
                        node_map[o] = node_id
                        core.add_node(CoreNode(id=node_id, labels=[], properties={}))
                
                # Handle rdf:type as labels
                if p == RDF.type and isinstance(o, URIRef):
                    subj_id = node_map[s]
                    type_uri = str(o)
                    if subj_id not in rdf_types:
                        rdf_types[subj_id] = []
                    rdf_types[subj_id].append(type_uri)
                elif isinstance(o, Literal):
                    # Literal becomes a property on the subject node
                    subj_id = node_map[s]
                    pred_str = str(p)
                    core.nodes[subj_id].properties[pred_str] = self._literal_to_core(o)
                else:
                    # Create an edge for the triple
                    edge_id = f"{node_map[s]}_{str(p)}_{node_map[o]}"
                    edge = CoreEdge(
                        id=edge_id,
                        source=node_map[s],
                        target=node_map[o],
                        label=str(p),
                        properties={}
                    )
                    core.add_edge(edge)
            
            # Apply rdf:type labels
            for node_id, types in rdf_types.items():
                if node_id in core.nodes:
                    core.nodes[node_id].labels = types
        
        elif mode == "reified_edges":
            # TODO: Implement reified_edges mode
            warnings.append("reified_edges mode not yet implemented")
        
        elif mode == "quads_with_context":
            # TODO: Implement quads_with_context mode
            warnings.append("quads_with_context mode not yet implemented")
        
        core.metadata["conversion_mode"] = mode
        core.metadata["source"] = "rdf"
        
        return ConversionResult(graph=core, warnings=warnings, mode=mode)
    
    def from_core(self, core: CoreGraph, mode: str = "simple", target_store: bool = None) -> ConversionResult:
        """
        Convert a CoreGraph to RDF.
        
        Args:
            core: The CoreGraph to convert
            mode: Conversion mode ("simple", "edge_properties_as_reification", etc.)
            target_store: If True, write to the configured store. If False, return a new Graph.
                         If None, use store if available, otherwise return a new Graph.
        
        Returns:
            ConversionResult with rdflib.Graph (or None if writing to store) and warnings
        """
        from rdflib import Graph, URIRef, Literal, RDF
        from kgcore.api.rdf_store import RDFStore
        
        if mode not in ["simple", "edge_properties_as_reification"]:
            raise ValueError(f"Unknown mode: {mode}")
        
        # Determine target: use store if available and requested, otherwise create new graph
        use_store = target_store if target_store is not None else (self._store is not None)
        
        if use_store and self._store is None:
            raise ValueError("Cannot write to store: no store configured")
        
        if use_store:
            # Write to store - clear it first or append?
            # For now, we'll append. Could add a clear_first parameter later.
            rdf_target = self._store
            result_graph = None  # Store doesn't return a graph object
        else:
            # Create new in-memory graph
            rdf_target = Graph()
            result_graph = rdf_target
        
        warnings = []
        
        if mode == "simple":
            # Simple mode: nodes become subjects/objects, edges become triples
            for node in core.nodes.values():
                node_uri = URIRef(str(node.id))
                
                # Add rdf:type for labels
                for label in node.labels:
                    if use_store:
                        rdf_target.add_triple(node_uri, RDF.type, URIRef(label))
                    else:
                        rdf_target.add((node_uri, RDF.type, URIRef(label)))
                
                # Add properties as triples with literals
                for prop, value in node.properties.items():
                    if isinstance(value, CoreLiteral):
                        lit = Literal(value.value, datatype=value.datatype, lang=value.language)
                    else:
                        lit = Literal(value)
                    
                    if use_store:
                        rdf_target.add_triple(node_uri, URIRef(prop), lit)
                    else:
                        rdf_target.add((node_uri, URIRef(prop), lit))
            
            # Add edges as triples
            for edge in core.edges.values():
                source_uri = URIRef(str(edge.source))
                target_uri = URIRef(str(edge.target))
                pred_uri = URIRef(edge.label)
                
                if use_store:
                    rdf_target.add_triple(source_uri, pred_uri, target_uri)
                else:
                    rdf_target.add((source_uri, pred_uri, target_uri))
                
                # Edge properties are lost in simple mode
                if edge.properties:
                    warnings.append(
                        f"Edge property information is not preserved in simple mode for edge {edge.id}"
                    )
        
        elif mode == "edge_properties_as_reification":
            # TODO: Implement edge properties as reification
            warnings.append("edge_properties_as_reification mode not yet implemented")
        
        # If using store, save it
        if use_store:
            rdf_target.save()
            # Return the store's graph for inspection if needed
            result_graph = rdf_target.get_graph()
        
        return ConversionResult(graph=result_graph, warnings=warnings, mode=mode)
    
    def get_available_modes(self) -> Dict[str, str]:
        """Get available conversion modes for RDF backend."""
        return self._modes
    
    def query(self, query_string: str, query_type: str = None) -> "QueryResult":
        """
        Execute a SPARQL query on the RDF graph.
        
        Args:
            query_string: SPARQL query string
            query_type: Optional query type hint (defaults to "sparql")
        
        Returns:
            QueryResult containing the query results
        
        Raises:
            ValueError: If no store is configured and query requires a graph
        """
        from kgcore.api.query import QueryResult, QueryError
        from kgcore.api.rdf_store import RDFStore
        
        query_type = query_type or "sparql"
        
        if query_type != "sparql":
            raise ValueError(f"RDFBackend only supports SPARQL queries, got: {query_type}")
        
        # Get the graph to query
        if self._store is not None:
            graph = self._store.get_graph()
        else:
            # Return QueryResult with error in metadata instead of raising
            return QueryResult(
                rows=[],
                columns=[],
                query_type=query_type,
                query_string=query_string,
                metadata={
                    "error": "Cannot execute query: no store configured. "
                             "Initialize RDFBackend with a store or use query() on a graph directly."
                }
            )
        
        try:
            from rdflib import Graph
            from rdflib.plugins.sparql import prepareQuery
            from rdflib.query import Result
            
            # Prepare and execute the query
            prepared_query = prepareQuery(query_string)
            result: Result = graph.query(prepared_query)
            
            # Convert rdflib Result to QueryResult
            columns = [str(var) for var in result.vars] if result.vars else []
            rows = []
            
            for row in result:
                row_dict = {}
                for var in result.vars:
                    value = row[var]
                    # Convert RDF terms to strings or appropriate Python types
                    if value is not None:
                        row_dict[str(var)] = str(value)
                    else:
                        row_dict[str(var)] = None
                rows.append(row_dict)
            
            return QueryResult(
                rows=rows,
                columns=columns,
                query_type="sparql",
                query_string=query_string,
                metadata={
                    "result_type": result.type,
                    "vars": [str(v) for v in result.vars] if result.vars else []
                }
            )
        
        except Exception as e:
            # Return error information in a QueryResult with metadata
            return QueryResult(
                rows=[],
                columns=[],
                query_type="sparql",
                query_string=query_string,
                metadata={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    def get_supported_query_types(self) -> List[str]:
        """Get list of supported query types (SPARQL for RDF)."""
        return ["sparql"]
    
    def _rdf_term_to_id(self, term) -> CoreId:
        """Convert an RDF term (URIRef, BNode, Literal) to a CoreId."""
        # Always convert to string to ensure consistent key types
        # URIRef might be a subclass of str, so we need to explicitly convert
        from rdflib import URIRef, BNode, Literal as RDFLiteral
        
        # For actual Python strings and ints, return as-is
        if type(term) is str:
            return term
        if type(term) is int:
            return term
        
        # For RDF terms (URIRef, BNode, Literal), always convert to string
        # even if they're str-like, to ensure consistent dictionary keys
        return str(term)
    
    def _literal_to_core(self, literal) -> CoreLiteral:
        """Convert an rdflib Literal to CoreLiteral."""
        from rdflib import Literal as RDFLiteral
        if isinstance(literal, RDFLiteral):
            return CoreLiteral(
                value=str(literal),
                datatype=str(literal.datatype) if literal.datatype else None,
                language=literal.language if hasattr(literal, 'language') and literal.language else None
            )
        return CoreLiteral(value=str(literal))


class PropertyGraphBackend(GraphBackend):
    """
    Adapter for Property Graph models (e.g., NetworkX, Neo4j).
    
    Provides conversion modes to explore mapping between property graphs
    and the CoreGraph IR.
    """
    
    def __init__(self):
        """Initialize the Property Graph backend adapter."""
        self._modes = {
            "simple": (
                "Direct mapping: nodes to nodes, edges to edges. "
                "Node labels map directly, edge properties preserved."
            ),
            "rdf_labels_as_node_labels": (
                "RDF-style labels (from rdf:type) become node labels in the property graph."
            ),
            "rdf_type_as_property": (
                "RDF types become properties instead of labels."
            ),
        }
    
    def to_core(self, graph, mode: str = "simple") -> ConversionResult:
        """
        Convert a property graph to CoreGraph.
        
        Args:
            graph: A property graph (implementation depends on backend)
            mode: Conversion mode
        
        Returns:
            ConversionResult with CoreGraph and warnings
        """
        # TODO: Implement property graph to CoreGraph conversion
        # This will depend on the specific property graph library (NetworkX, Neo4j, etc.)
        raise NotImplementedError("Property graph conversion not yet implemented")
    
    def from_core(self, core: CoreGraph, mode: str = "simple") -> ConversionResult:
        """
        Convert a CoreGraph to a property graph.
        
        Args:
            core: The CoreGraph to convert
            mode: Conversion mode
        
        Returns:
            ConversionResult with property graph and warnings
        """
        # TODO: Implement CoreGraph to property graph conversion
        raise NotImplementedError("Property graph conversion not yet implemented")
    
    def get_available_modes(self) -> Dict[str, str]:
        """Get available conversion modes for Property Graph backend."""
        return self._modes
    
    def query(self, query_string: str, query_type: str = None) -> "QueryResult":
        """
        Execute a Cypher query on the property graph.
        
        Args:
            query_string: Cypher query string
            query_type: Optional query type hint (defaults to "cypher")
        
        Returns:
            QueryResult containing the query results
        
        Raises:
            NotImplementedError: Cypher querying not yet implemented
        """
        from kgcore.api.query import QueryResult
        
        query_type = query_type or "cypher"
        
        if query_type != "cypher":
            raise ValueError(f"PropertyGraphBackend only supports Cypher queries, got: {query_type}")
        
        # TODO: Implement Cypher querying
        # This will depend on the specific property graph library (Neo4j, NetworkX, etc.)
        raise NotImplementedError(
            "Cypher querying not yet implemented. "
            "This requires a property graph library with Cypher support (e.g., Neo4j driver)."
        )
    
    def get_supported_query_types(self) -> List[str]:
        """Get list of supported query types (Cypher for Property Graphs)."""
        return ["cypher"]
