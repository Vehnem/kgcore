# Core Graph Model (CGM)

The Core Graph Model (CGM) is an intermediate representation (IR) designed for research and teaching purposes. It serves as a bridge between different graph models (RDF, Property Graphs, etc.) and makes information loss and design tradeoffs explicit.

## Overview

The CGM provides a minimal, precise representation that is:
- Simple enough to explain on a whiteboard
- Structured enough to express common patterns
- Stable enough to support multiple adapters

Think of it as "the IR for a graph compiler" that enables experimentation with graph representations.

## Core Classes

### CoreNode

Represents a node in the graph with an ID, labels, and properties.

```python
from kgcore.api.cgm import CoreNode, CoreLiteral

# Create a node
node = CoreNode(
    id="person1",
    labels=["Person", "Agent"],
    properties={
        "name": "Alice",
        "age": 30,
        "email": CoreLiteral(value="alice@example.com", datatype="xsd:string")
    }
)
```

### CoreEdge

Represents an edge (relationship) with an ID, source, target, label, and properties.

```python
from kgcore.api.cgm import CoreEdge

# Create an edge
edge = CoreEdge(
    id="edge1",
    source="person1",
    target="person2",
    label="knows",
    properties={
        "since": "2020",
        "confidence": 0.9
    }
)
```

### CoreLiteral

Represents a typed literal value with optional datatype and language tag.

```python
from kgcore.api.cgm import CoreLiteral

# Simple literal
lit1 = CoreLiteral(value="Hello")

# Typed literal
lit2 = CoreLiteral(
    value="42",
    datatype="http://www.w3.org/2001/XMLSchema#integer"
)

# Language-tagged literal
lit3 = CoreLiteral(
    value="Bonjour",
    language="fr"
)
```

### CoreGraph

Container for nodes and edges with metadata.

```python
from kgcore.api.cgm import CoreGraph, CoreNode, CoreEdge

# Create an empty graph
graph = CoreGraph()

# Add nodes
alice = CoreNode(id="alice", labels=["Person"], properties={"name": "Alice"})
bob = CoreNode(id="bob", labels=["Person"], properties={"name": "Bob"})
graph.add_node(alice)
graph.add_node(bob)

# Add edge
knows = CoreEdge(id="e1", source="alice", target="bob", label="knows")
graph.add_edge(knows)

# Access nodes and edges
print(f"Nodes: {len(graph.nodes)}")
print(f"Edges: {len(graph.edges)}")

# Get specific node/edge
node = graph.get_node("alice")
edge = graph.get_edge("e1")

# Add metadata
graph.metadata["source"] = "manual_entry"
graph.metadata["version"] = "1.0"
```

## Working with CoreGraph

### Basic Operations

```python
from kgcore.api.cgm import CoreGraph, CoreNode, CoreEdge

graph = CoreGraph()

# Add nodes
for i in range(3):
    node = CoreNode(
        id=f"node{i}",
        labels=["Entity"],
        properties={"index": i}
    )
    graph.add_node(node)

# Add edges
for i in range(2):
    edge = CoreEdge(
        id=f"edge{i}",
        source=f"node{i}",
        target=f"node{i+1}",
        label="connects"
    )
    graph.add_edge(edge)

# Iterate over nodes
for node_id, node in graph.nodes.items():
    print(f"{node_id}: {node.labels}")

# Iterate over edges
for edge_id, edge in graph.edges.items():
    print(f"{edge_id}: {edge.source} -> {edge.target}")
```

### Node and Edge Properties

Properties can contain plain values or `CoreLiteral` instances:

```python
from kgcore.api.cgm import CoreNode, CoreLiteral

node = CoreNode(
    id="data1",
    labels=["DataPoint"],
    properties={
        # Plain value
        "name": "Temperature",
        
        # Typed literal
        "value": CoreLiteral(
            value="25.5",
            datatype="http://www.w3.org/2001/XMLSchema#float"
        ),
        
        # Language-tagged literal
        "description": CoreLiteral(
            value="Temperature reading",
            language="en"
        )
    }
)
```

## Use Cases

### 1. Research and Teaching

The CGM is designed for exploring graph representation tradeoffs:

```python
# Compare different conversion strategies
from kgcore.api.cgm import RDFBackend
from rdflib import Graph

rdf_graph = Graph()  # ... add triples ...

backend = RDFBackend()

# Try different modes
for mode in ["simple", "reified_edges", "quads_with_context"]:
    result = backend.to_core(rdf_graph, mode=mode)
    print(f"Mode {mode}: {len(result.graph.nodes)} nodes, {len(result.graph.edges)} edges")
    if result.warnings:
        print(f"  Warnings: {result.warnings}")
```

### 2. Graph Conversion Bridge

Use CGM to convert between different graph models:

```python
from kgcore.api.cgm import RDFBackend, CoreGraph
from kgcore.api.rdf_store import InMemoryRDFStore

# RDF -> CoreGraph -> (future: Property Graph)
store = InMemoryRDFStore()
backend = RDFBackend(store=store)

# Load RDF data
# ... populate store ...

# Convert to CoreGraph
core = backend.to_core(mode="simple").graph

# Work with CoreGraph
# ... manipulate core ...

# Convert back to RDF
backend.from_core(core, mode="simple", target_store=True)
```

### 3. System Graph Tracking

The system graph uses CGM internally:

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore

# Create recorder with file persistence
store = FileRDFStore("system_kg.ttl", format="turtle", auto_save=True)
recorder = SystemRecorder(store=store)

# Register functions, track runs
# ... use decorators ...

# Access the CoreGraph
core = recorder.get_graph()
print(f"System graph: {len(core.nodes)} nodes, {len(core.edges)} edges")
```

## Best Practices

1. **Use CoreGraph for conversions**: When converting between graph models, use CGM as the intermediate representation.

2. **Track information loss**: Always check `ConversionResult.warnings` to understand what information might be lost.

3. **Use appropriate modes**: Different conversion modes preserve different information. Choose based on your needs.

4. **Metadata for provenance**: Use `CoreGraph.metadata` to track where data came from and how it was processed.

5. **Hashable IDs**: CoreGraph uses hashable IDs, so you can use strings, integers, or tuples as node/edge IDs.

## See Also

- [RDF Backend](./rdf_backend.md) - Converting between RDF and CoreGraph
- [Conversion Modes](./conversion_modes.md) - Understanding different conversion strategies
- [System Graph](./system_graph.md) - Using CGM for system graph tracking

