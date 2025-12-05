# Model Converters

Utilities for converting between the high-level KGGraph API and the Core Graph Model (CGM).

## Overview

kgcore has two graph representations:
1. **High-level API** (`model/`) - User-facing, simple API (KGEntity, KGRelation, KGGraph)
2. **Core Graph Model** (`api/cgm`) - Research/teaching IR (CoreNode, CoreEdge, CoreGraph)

Converters allow you to move between these representations.

## Basic Conversions

### Entity ↔ Node

```python
from kgcore.model.base import KGEntity
from kgcore.model.converters import kg_entity_to_core_node, core_node_to_kg_entity
from kgcore.api.cgm import CoreNode

# High-level API entity
entity = KGEntity(
    id="person1",
    labels=["Person"],
    props={"name": "Alice", "age": 30}
)

# Convert to CGM node
node = kg_entity_to_core_node(entity)
print(f"Node ID: {node.id}")
print(f"Node labels: {node.labels}")
print(f"Node properties: {node.properties}")

# Convert back
entity2 = core_node_to_kg_entity(node)
print(f"Entity ID: {entity2.id}")
```

### Relation ↔ Edge

```python
from kgcore.model.base import KGRelation
from kgcore.model.converters import kg_relation_to_core_edge, core_edge_to_kg_relation
from kgcore.api.cgm import CoreEdge

# High-level API relation
relation = KGRelation(
    id="rel1",
    type="KNOWS",  # Note: uses 'type'
    source="person1",
    target="person2",
    props={"since": "2020"}
)

# Convert to CGM edge
edge = kg_relation_to_core_edge(relation)
print(f"Edge label: {edge.label}")  # Note: uses 'label'
print(f"Edge properties: {edge.properties}")

# Convert back
relation2 = core_edge_to_kg_relation(edge)
print(f"Relation type: {relation2.type}")
```

### Graph ↔ Graph

```python
from kgcore.model.converters import kg_graph_to_core_graph, core_graph_to_kg_graph
from kgcore.api import KG
from kgcore.api.cgm import CoreGraph

# High-level API graph
kg = KG()
entity = kg.create_entity(["Person"], {"name": "Alice"})
relation = kg.create_relation("KNOWS", entity.id, "person2", {})

# Convert to CGM
core = kg_graph_to_core_graph(kg)
print(f"CoreGraph: {len(core.nodes)} nodes, {len(core.edges)} edges")

# Convert back to high-level API
kg2 = KG()
core_graph_to_kg_graph(core, kg2)
entities = kg2.find_entities("Person")
print(f"Found {len(entities)} persons")
```

## Handling Literals

### Lit ↔ CoreLiteral

```python
from kgcore.common.types import Lit, lit_to_core_literal, core_literal_to_lit
from kgcore.api.cgm import CoreLiteral

# High-level Lit
lit = Lit(value="42", datatype="xsd:integer")

# Convert to CoreLiteral
core_lit = lit_to_core_literal(lit)
print(f"CoreLiteral: {core_lit.value}, {core_lit.datatype}")

# Convert back (language tag is lost)
lit2 = core_literal_to_lit(core_lit)
print(f"Lit: {lit2.value}, {lit2.datatype}")
```

### Properties with Literals

```python
from kgcore.model.base import KGEntity
from kgcore.common.types import Lit
from kgcore.model.converters import kg_entity_to_core_node

# Entity with Lit in properties
entity = KGEntity(
    id="data1",
    labels=["DataPoint"],
    props={
        "name": "Temperature",
        "value": Lit(value="25.5", datatype="xsd:float")
    }
)

# Convert to node (Lit becomes CoreLiteral)
node = kg_entity_to_core_node(entity)
print(f"Property type: {type(node.properties['value'])}")  # CoreLiteral
```

## Complete Workflow Example

Convert between models in a complete workflow:

```python
from kgcore.api import KG
from kgcore.model.converters import kg_graph_to_core_graph
from kgcore.api.cgm import RDFBackend
from kgcore.api.rdf_store import FileRDFStore

# 1. Create data with high-level API
kg = KG()
alice = kg.create_entity(["Person"], {"name": "Alice", "age": 30})
bob = kg.create_entity(["Person"], {"name": "Bob"})
kg.create_relation("KNOWS", alice.id, bob.id, {"since": "2020"})

# 2. Convert to CGM for research/analysis
core = kg_graph_to_core_graph(kg)
print(f"CGM: {len(core.nodes)} nodes, {len(core.edges)} edges")

# 3. Convert CGM to RDF for persistence
store = FileRDFStore("output.ttl", format="turtle", auto_save=True)
backend = RDFBackend(store=store)
backend.from_core(core, mode="simple", target_store=True)

# 4. Query with SPARQL
result = backend.query("""
    PREFIX ex: <http://example.org/>
    SELECT ?person ?name
    WHERE {
        ?person a ex:Person .
        ?person ex:name ?name .
    }
""")

for row in result:
    print(f"{row['person']}: {row['name']}")
```

## Differences Between Models

### Naming Conventions

| High-level API | Core Graph Model |
|---------------|------------------|
| `KGRelation.type` | `CoreEdge.label` |
| `KGEntity.props` | `CoreNode.properties` |
| `KGRelation.props` | `CoreEdge.properties` |

### ID Types

- **High-level API**: `KGId = str` (always string)
- **CGM**: `CoreId = Hashable` (string, int, tuple, etc.)

### Literal Support

- **High-level API**: `Lit` (value, datatype) - no language tag
- **CGM**: `CoreLiteral` (value, datatype, language) - full RDF literal support

## When to Use Converters

### Use High-level API when:
- Building applications
- Working with backends (memory, rdf_file, etc.)
- Need simple, straightforward API
- Don't need to explore graph representation tradeoffs

### Use CGM when:
- Converting between graph models
- Researching graph representation tradeoffs
- Teaching graph model differences
- Need to preserve edge properties and identity
- Working with system graph

### Use Converters when:
- Need to bridge between the two models
- Migrating from high-level API to CGM
- Integrating with existing code using high-level API
- Need to use CGM features (edge properties) with high-level API data

## Best Practices

1. **Choose the right model**: Use high-level API for applications, CGM for research/conversions.

2. **Convert at boundaries**: Convert at module boundaries, not inside tight loops.

3. **Preserve IDs**: When converting back and forth, be aware that IDs may change format.

4. **Handle literals**: Be aware that `Lit` doesn't support language tags (lost in conversion).

5. **Check for information loss**: Some conversions may lose information (e.g., edge properties in simple mode).

6. **Use appropriate mode**: When converting CGM to RDF, choose the mode that preserves what you need.

## See Also

- [Core Graph Model](./core_graph_model.md) - Understanding CGM
- [RDF Backend](./rdf_backend.md) - Converting CGM to/from RDF
- [Conversion Modes](./conversion_modes.md) - Understanding conversion tradeoffs

