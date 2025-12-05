# RDF Backend

The RDF Backend provides conversion between RDF graphs and the Core Graph Model (CGM), enabling you to work with RDF data through the CGM IR.

## Overview

The `RDFBackend` class implements the `GraphBackend` interface and provides:
- Conversion from RDF (rdflib.Graph) to CoreGraph
- Conversion from CoreGraph to RDF
- Multiple conversion modes with different tradeoffs
- SPARQL query support
- Integration with RDF storage backends

## Basic Usage

### Converting RDF to CoreGraph

```python
from kgcore.api.cgm import RDFBackend
from rdflib import Graph, URIRef, Literal, RDF, Namespace

# Create an RDF graph
rdf_graph = Graph()
EX = Namespace("http://example.org/")
alice = URIRef("http://example.org/alice")
bob = URIRef("http://example.org/bob")

# Add triples
rdf_graph.add((alice, RDF.type, EX.Person))
rdf_graph.add((alice, EX.name, Literal("Alice")))
rdf_graph.add((alice, EX.age, Literal(30)))
rdf_graph.add((alice, EX.knows, bob))
rdf_graph.add((bob, RDF.type, EX.Person))
rdf_graph.add((bob, EX.name, Literal("Bob")))

# Convert to CoreGraph
backend = RDFBackend()
result = backend.to_core(rdf_graph, mode="simple")
core = result.graph

# Work with CoreGraph
print(f"Nodes: {len(core.nodes)}")
print(f"Edges: {len(core.edges)}")

# Check for warnings
if result.warnings:
    print(f"Warnings: {result.warnings}")
```

### Converting CoreGraph to RDF

```python
from kgcore.api.cgm import RDFBackend, CoreGraph, CoreNode, CoreEdge

# Create a CoreGraph
core = CoreGraph()
alice = CoreNode(
    id="alice",
    labels=["http://example.org/Person"],
    properties={
        "http://example.org/name": "Alice",
        "http://example.org/age": 30
    }
)
bob = CoreNode(
    id="bob",
    labels=["http://example.org/Person"],
    properties={"http://example.org/name": "Bob"}
)
core.add_node(alice)
core.add_node(bob)
core.add_edge(CoreEdge(
    id="e1",
    source="alice",
    target="bob",
    label="http://example.org/knows"
))

# Convert to RDF
backend = RDFBackend()
result = backend.from_core(core, mode="simple")
rdf_graph = result.graph

# rdf_graph is now an rdflib.Graph
print(f"RDF triples: {len(rdf_graph)}")

# Check for warnings (e.g., lost edge properties)
if result.warnings:
    print(f"Warnings: {result.warnings}")
```

## Using RDF Storage

### In-Memory Storage

```python
from kgcore.api.cgm import RDFBackend
from kgcore.api.rdf_store import InMemoryRDFStore

# Create store and backend
store = InMemoryRDFStore()
backend = RDFBackend(store=store)

# Create CoreGraph
core = CoreGraph()
# ... add nodes and edges ...

# Convert and store
backend.from_core(core, mode="simple", target_store=True)

# Read back
result = backend.to_core(mode="simple")
retrieved_core = result.graph
```

### File-Based Storage

```python
from kgcore.api.cgm import RDFBackend
from kgcore.api.rdf_store import FileRDFStore

# Create file store with auto-save
store = FileRDFStore("my_graph.ttl", format="turtle", auto_save=True)
backend = RDFBackend(store=store)

# Convert and save
backend.from_core(core, mode="simple", target_store=True)
# File is automatically saved

# Load from file
store2 = FileRDFStore("my_graph.ttl", format="turtle")
backend2 = RDFBackend(store=store2)
result = backend2.to_core(mode="simple")
```

## Round-Trip Conversion

Test what information is preserved in round-trip conversions:

```python
from kgcore.api.cgm import RDFBackend
from rdflib import Graph, URIRef, Literal, RDF, Namespace

# Create original RDF
original = Graph()
EX = Namespace("http://example.org/")
alice = URIRef("http://example.org/alice")
original.add((alice, RDF.type, EX.Person))
original.add((alice, EX.name, Literal("Alice")))

# Round-trip
backend = RDFBackend()
core_result = backend.to_core(original, mode="simple")
rdf_result = backend.from_core(core_result.graph, mode="simple")

round_tripped = rdf_result.graph

# Compare
original_triples = set(original)
round_tripped_triples = set(round_tripped)

print(f"Original: {len(original_triples)} triples")
print(f"Round-tripped: {len(round_tripped_triples)} triples")
print(f"Preserved: {len(original_triples & round_tripped_triples)}")
print(f"Lost: {len(original_triples - round_tripped_triples)}")
print(f"Added: {len(round_tripped_triples - original_triples)}")
```

## Conversion Modes

Different modes preserve different information. See [Conversion Modes](./conversion_modes.md) for details.

```python
# Simple mode (default)
result = backend.to_core(rdf_graph, mode="simple")

# Reified edges mode (preserves edge metadata)
result = backend.to_core(rdf_graph, mode="reified_edges")

# Quads with context mode (preserves named graphs)
result = backend.to_core(rdf_graph, mode="quads_with_context")
```

## SPARQL Queries

Query RDF data through the backend:

```python
from kgcore.api.cgm import RDFBackend
from kgcore.api.rdf_store import InMemoryRDFStore

# Setup
store = InMemoryRDFStore()
backend = RDFBackend(store=store)

# Load data (via CoreGraph or directly)
# ... populate store ...

# Query with SPARQL
query = """
PREFIX ex: <http://example.org/>
SELECT ?person ?name ?age
WHERE {
    ?person a ex:Person .
    ?person ex:name ?name .
    OPTIONAL { ?person ex:age ?age }
}
"""

result = backend.query(query)

# Access results
print(f"Found {len(result)} results")
for row in result:
    print(f"{row['person']}: {row['name']} (age: {row.get('age', 'unknown')})")

# Convert to dictionary keyed by person
by_person = result.to_dict("person")
```

### Query Result Methods

```python
# Get as list
rows = result.to_list()

# Get as dictionary (keyed by column)
by_id = result.to_dict("person")

# Iterate
for row in result:
    print(row)

# Access metadata
print(f"Query type: {result.query_type}")
print(f"Columns: {result.columns}")
print(f"Metadata: {result.metadata}")
```

## Error Handling

```python
from kgcore.api.cgm import RDFBackend

backend = RDFBackend(store=store)

# Invalid query
result = backend.query("INVALID SPARQL QUERY")
if "error" in result.metadata:
    print(f"Query error: {result.metadata['error']}")

# Missing store
backend_no_store = RDFBackend()
try:
    result = backend_no_store.query("SELECT ?s WHERE { ?s ?p ?o }")
except ValueError as e:
    print(f"Error: {e}")
```

## Supported Query Types

```python
from kgcore.api.cgm import RDFBackend

backend = RDFBackend(store=store)
supported = backend.get_supported_query_types()
print(f"Supported: {supported}")  # ['sparql']
```

## Available Modes

```python
from kgcore.api.cgm import RDFBackend

backend = RDFBackend()
modes = backend.get_available_modes()
for mode, description in modes.items():
    print(f"{mode}: {description}")
```

## Best Practices

1. **Choose appropriate mode**: Use `simple` for basic conversions, `reified_edges` to preserve edge properties, `quads_with_context` for named graphs.

2. **Check warnings**: Always check `ConversionResult.warnings` to understand information loss.

3. **Use stores for persistence**: Use `RDFStore` implementations for persistent storage.

4. **Round-trip testing**: Test round-trip conversions to verify what's preserved.

5. **Query before convert**: For large graphs, query what you need rather than converting everything.

## See Also

- [Core Graph Model](./core_graph_model.md) - Understanding the CGM IR
- [RDF Storage](./rdf_storage.md) - Storage backends
- [Conversion Modes](./conversion_modes.md) - Detailed mode documentation
- [Query Support](./query_support.md) - SPARQL query details

