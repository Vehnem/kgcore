# kgcore Documentation

Welcome to the kgcore documentation! kgcore is a research and teaching library for working with knowledge graphs, providing a unified API and tools for exploring graph representation tradeoffs.

## Quick Links

- [CLI Reference](./cli.md) - Command-line interface for working with knowledge graphs
- [Core Graph Model (CGM)](./core_graph_model.md) - The intermediate representation for bridging graph models
- [RDF Backend](./rdf_backend.md) - Converting between RDF and CoreGraph
- [RDF Storage](./rdf_storage.md) - Storage backends for RDF data
- [Query Support](./query_support.md) - SPARQL queries and query interfaces
- [Conversion Modes](./conversion_modes.md) - Understanding different conversion strategies
- [System Graph](./system_graph.md) - Tracking Python code semantics and execution
- [Model Converters](./model_converters.md) - Converting between high-level API and CGM

## Overview

kgcore provides two main graph representations:

### 1. High-level API (`kgcore.model`)

User-facing, model-agnostic API for building applications:

```python
from kgcore.api import KG

kg = KG()
entity = kg.create_entity(["Person"], {"name": "Alice"})
relation = kg.create_relation("KNOWS", entity.id, "person2", {})
```

### 2. Core Graph Model (`kgcore.api.cgm`)

Research/teaching IR for exploring graph representation tradeoffs:

```python
from kgcore.api.cgm import CoreGraph, CoreNode, CoreEdge

core = CoreGraph()
node = CoreNode(id="alice", labels=["Person"], properties={"name": "Alice"})
edge = CoreEdge(id="e1", source="alice", target="bob", label="knows")
```

## Key Features

- **Command-Line Interface** - Full-featured CLI for format conversion, querying, and graph mutations
- **Core Graph Model (CGM)** - Intermediate representation for bridging RDF and Property Graphs
- **Conversion Modes** - Multiple strategies with explicit information loss tracking
- **RDF Storage** - In-memory and file-based storage with extensible interface
- **Query Support** - SPARQL for RDF, Cypher (planned) for Property Graphs
- **System Graph** - Track Python code semantics and execution
- **Model Converters** - Convert between high-level API and CGM

## Getting Started

### Installation

```bash
pip install kgcore
```

### Basic Usage

```python
from kgcore.api import KG

# Create a knowledge graph
kg = KG()

# Create entities
alice = kg.create_entity(["Person"], {"name": "Alice", "age": 30})
bob = kg.create_entity(["Person"], {"name": "Bob"})

# Create relations
kg.create_relation("KNOWS", alice.id, bob.id, {"since": 2020})

# Query
persons = kg.find_entities("Person")
for person in persons:
    print(f"{person.props['name']}")
```

### Using Core Graph Model

```python
from kgcore.api.cgm import CoreGraph, CoreNode, CoreEdge, RDFBackend
from kgcore.api.rdf_store import InMemoryRDFStore

# Create CoreGraph
core = CoreGraph()
alice = CoreNode(id="alice", labels=["Person"], properties={"name": "Alice"})
core.add_node(alice)

# Convert to RDF
store = InMemoryRDFStore()
backend = RDFBackend(store=store)
backend.from_core(core, mode="simple", target_store=True)

# Query with SPARQL
result = backend.query("SELECT ?s WHERE { ?s ?p ?o }")
```

## Documentation Structure

- **CLI Reference** - Command-line interface usage and examples
- **Core Graph Model** - Understanding the IR and its classes
- **RDF Backend** - Converting between RDF and CoreGraph
- **RDF Storage** - Storage backends and persistence
- **Query Support** - Querying graphs with SPARQL
- **Conversion Modes** - Understanding conversion tradeoffs
- **System Graph** - Tracking code semantics
- **Model Converters** - Converting between models

## Research and Teaching Focus

kgcore is designed as a research and teaching library:

- **Explicit Information Loss**: Conversion modes document what's preserved/lost
- **Multiple Strategies**: Compare different conversion approaches
- **Round-trip Testing**: Verify what's preserved in conversions
- **Educational Examples**: Clear examples for learning graph models

## Examples

See the `src/kgcore/examples/` directory for comprehensive examples:

- `01_minimal_inmemory.py` - Basic in-memory graph usage
- `02_rdf_file_persistence.py` - RDF file persistence
- `07_core_graph_model.py` - Core Graph Model usage

## Contributing

This is a research library focused on:
- Making graph representation tradeoffs explicit
- Providing educational examples
- Supporting experimentation with different graph models

For questions or discussions, please open an issue on the repository.

