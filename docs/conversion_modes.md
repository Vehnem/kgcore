# Conversion Modes

Conversion modes define different strategies for converting between graph models, each with different tradeoffs in terms of what information is preserved or lost.

## Overview

Different conversion modes:
- Preserve different aspects of the source graph
- Have different performance characteristics
- May lose or approximate certain information
- Are documented with explicit `preserves`, `loses`, and `warnings`

## RDF to CoreGraph Modes

### Simple Mode

**Default mode** - Each RDF triple becomes one CoreEdge. Simple and direct.

```python
from kgcore.api.cgm import RDFBackend
from rdflib import Graph, URIRef, Literal, RDF, Namespace

rdf_graph = Graph()
EX = Namespace("http://example.org/")
alice = URIRef("http://example.org/alice")

rdf_graph.add((alice, RDF.type, EX.Person))
rdf_graph.add((alice, EX.name, Literal("Alice")))

backend = RDFBackend()
result = backend.to_core(rdf_graph, mode="simple")
```

**Preserves:**
- All triples (as edges)
- rdf:type information (as node labels)
- Literal values (as node properties)
- URIs and blank nodes (as node IDs)

**Loses:**
- Named graph context
- RDF reification
- RDF* (quoted triples)
- Edge properties (if converting back)

**Use when:**
- You need a simple, direct conversion
- Named graphs and reification aren't important
- You want maximum compatibility

### Reified Edges Mode

RDF reification gets turned into explicit edge nodes with properties.

```python
result = backend.to_core(rdf_graph, mode="reified_edges")
```

**Preserves:**
- RDF reification structure
- Metadata on reified statements

**Loses:**
- Direct triple representation
- Some RDF reification patterns may not round-trip perfectly

**Warnings:**
- Increases graph size significantly
- May create cycles in the graph

**Use when:**
- You need to preserve reification metadata
- You're working with reified RDF data

### Quads with Context Mode

Named graphs or graph names become graph-level properties or edge properties.

```python
result = backend.to_core(rdf_graph, mode="quads_with_context")
```

**Preserves:**
- Named graph information
- Quad context
- Graph-level metadata

**Loses:**
- Direct named graph structure (becomes properties)

**Warnings:**
- Named graphs become properties, not first-class objects

**Use when:**
- You need to preserve named graph context
- You're working with RDF datasets (multiple named graphs)

## CoreGraph to RDF Modes

### Simple Mode

Direct mapping: nodes become subjects/objects, edges become triples.

```python
from kgcore.api.cgm import RDFBackend, CoreGraph, CoreNode, CoreEdge

core = CoreGraph()
# ... add nodes and edges ...

backend = RDFBackend()
result = backend.from_core(core, mode="simple")
```

**Preserves:**
- All nodes and edges
- Node labels (as rdf:type)
- Node properties (as triples with literals)

**Loses:**
- Edge properties
- Edge identity (edges become anonymous triples)

**Warnings:**
- Edge properties are dropped
- Edge IDs are not preserved

**Use when:**
- Edge properties aren't needed
- You want simple RDF output

### Edge Properties as Reification Mode

Edge properties are preserved using RDF reification.

```python
result = backend.from_core(core, mode="edge_properties_as_reification")
```

**Preserves:**
- Edge properties
- Edge identity (via reification)

**Loses:**
- Simple triple structure (becomes more complex)

**Warnings:**
- Significantly increases graph size
- Requires RDF reification support in queries

**Use when:**
- You need to preserve edge properties
- Edge identity is important

## Property Graph Modes (Planned)

### Simple Mode

Direct mapping: nodes to nodes, edges to edges.

**Preserves:**
- All nodes and edges
- Node labels
- Node properties
- Edge properties
- Edge identity

**Loses:**
- Nothing (ideal mapping)

### RDF Labels as Node Labels Mode

RDF-style labels (from rdf:type) become node labels.

**Preserves:**
- rdf:type information (as labels)

**Warnings:**
- Multiple rdf:type values become multiple labels

### RDF Type as Property Mode

RDF types become properties instead of labels.

**Preserves:**
- rdf:type information (as properties)

**Loses:**
- Label-based type information

**Warnings:**
- Type information must be queried via properties, not labels

## Getting Mode Information

### List Available Modes

```python
from kgcore.api.modes import list_modes

# List RDF to CoreGraph modes
rdf_to_core_modes = list_modes("rdf", "to_core")
print(rdf_to_core_modes)  # ['simple', 'reified_edges', 'quads_with_context']

# List CoreGraph to RDF modes
core_to_rdf_modes = list_modes("rdf", "from_core")
print(core_to_rdf_modes)  # ['simple', 'edge_properties_as_reification']
```

### Get Mode Details

```python
from kgcore.api.modes import get_mode_info

# Get information about a specific mode
info = get_mode_info("rdf", "to_core", "simple")
print(f"Name: {info['name']}")
print(f"Description: {info['description']}")
print(f"Preserves: {info['preserves']}")
print(f"Loses: {info['loses']}")
print(f"Warnings: {info['warnings']}")
```

### From Backend

```python
from kgcore.api.cgm import RDFBackend

backend = RDFBackend()
modes = backend.get_available_modes()
for mode, description in modes.items():
    print(f"{mode}: {description}")
```

## Checking Conversion Results

Always check warnings to understand information loss:

```python
from kgcore.api.cgm import RDFBackend, CoreGraph, CoreNode, CoreEdge

# Create CoreGraph with edge properties
core = CoreGraph()
core.add_node(CoreNode(id="a", labels=[], properties={}))
core.add_node(CoreNode(id="b", labels=[], properties={}))
core.add_edge(CoreEdge(
    id="e1",
    source="a",
    target="b",
    label="knows",
    properties={"confidence": 0.9}  # This will be lost in simple mode
))

# Convert to RDF
backend = RDFBackend()
result = backend.from_core(core, mode="simple")

# Check warnings
if result.warnings:
    print("Information loss detected:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

## Mode Comparison Example

Compare different modes to see tradeoffs:

```python
from kgcore.api.cgm import RDFBackend
from rdflib import Graph

rdf_graph = Graph()
# ... populate graph ...

backend = RDFBackend()

# Try different modes
for mode in ["simple", "reified_edges", "quads_with_context"]:
    result = backend.to_core(rdf_graph, mode=mode)
    core = result.graph
    
    print(f"\nMode: {mode}")
    print(f"  Nodes: {len(core.nodes)}")
    print(f"  Edges: {len(core.edges)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    if result.warnings:
        for warning in result.warnings:
            print(f"    - {warning}")
```

## Round-Trip Testing

Test what's preserved in round-trips:

```python
from kgcore.api.cgm import RDFBackend
from rdflib import Graph

original = Graph()
# ... add triples ...

backend = RDFBackend()

# Test round-trip with different modes
for mode in ["simple", "edge_properties_as_reification"]:
    # RDF -> Core -> RDF
    core_result = backend.to_core(original, mode="simple")
    rdf_result = backend.from_core(core_result.graph, mode=mode)
    
    round_tripped = rdf_result.graph
    
    # Compare
    original_set = set(original)
    round_tripped_set = set(round_tripped)
    
    preserved = len(original_set & round_tripped_set)
    lost = len(original_set - round_tripped_set)
    added = len(round_tripped_set - original_set)
    
    print(f"Mode {mode}:")
    print(f"  Preserved: {preserved}/{len(original_set)}")
    print(f"  Lost: {lost}")
    print(f"  Added: {added}")
```

## Best Practices

1. **Start with simple mode**: Use `simple` mode unless you need specific features.

2. **Check warnings**: Always review `ConversionResult.warnings` to understand information loss.

3. **Test round-trips**: Verify what's preserved in round-trip conversions for your use case.

4. **Document mode choice**: If using a non-default mode, document why in your code.

5. **Consider performance**: Some modes (like reification) significantly increase graph size.

6. **Match modes**: When round-tripping, consider using compatible modes.

## See Also

- [RDF Backend](./rdf_backend.md) - Using conversion modes
- [Core Graph Model](./core_graph_model.md) - Understanding the IR
- [RDF Storage](./rdf_storage.md) - Storing converted data

