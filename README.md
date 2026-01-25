# KGcore

**KGcore** is a Python library for working with Knowledge Graphs. It provides a unified API for different graph models (RDF, Property Graphs) and backends, making it easy to create, query, and manipulate knowledge graph data.

## Installation

```bash
pip install kgcore
```

Or install from source:

```bash
git clone <repository-url>
cd kgcore
pip install -e .
```

## Core Concepts

KGcore is organized into three main layers:

1. **API Layer** (`kgcore.api`) - High-level interface for working with knowledge graphs
2. **Model Layer** (`kgcore.model`) - Implementations for different graph models (RDF, Property Graphs)
3. **Backend Layer** (`kgcore.backend`) - Storage backends (in-memory, RDF files, databases)

## Quick Start

### Basic Knowledge Graph Operations

```python
from kgcore.api import KnowledgeGraph, KGProperty
from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel

# Create backend and model
backend = RDFLibBackend()
model = RDFBaseModel()
kg = KnowledgeGraph(model=model, backend=backend)

# Create entities
alice = kg.create_entity(
    id="http://example.org/alice",
    types=["http://example.org/Person"],
    properties=[KGProperty(key="http://example.org/name", value="Alice")]
)

# Create relations
kg.create_relation(
    source="http://example.org/alice",
    target="http://example.org/bob",
    type="http://example.org/knows"
)

# Query entities
entity = kg.read_entity("http://example.org/alice")
neighbors = kg.get_neighbors("http://example.org/alice", predicate="http://example.org/knows")

kg.close()
```

### System Graph - Tracking Python Code

KGcore includes a **System Graph** module that lets you track Python code semantics, function calls, and execution metadata in a knowledge graph.

```python
from kgcore.backend.rdf.rdf_rdflib import RDFLibBackend
from kgcore.model.rdf.rdf_base import RDFBaseModel
from kgcore.system import SystemRecorder, set_default_recorder, class_, event, pydantic_model
from pydantic import BaseModel, Field

# Set up recorder
backend = RDFLibBackend()
model = RDFBaseModel()
recorder = SystemRecorder(model=model, backend=backend)
set_default_recorder(recorder)

# Register a class
@class_("A data processor class")
class DataProcessor:
    """Processes data."""
    
    @event("Process data", track_calls=True)
    def process(self, data: str) -> dict:
        """Process input data."""
        return {"processed": data}

# Register a Pydantic model
@pydantic_model("User profile model")
class User(BaseModel):
    """User profile."""
    name: str = Field(description="User name")
    email: str = Field(description="User email")

# Use the code - calls are automatically tracked
processor = DataProcessor()
result = processor.process("test_data")

# Store Pydantic instances
user = User(name="Alice", email="alice@example.com")
recorder.store_pydantic_instance(user, instance_id="user-001")

recorder.close()
```

## Features

- **Unified API** - Same interface for different graph models (RDF, Property Graphs)
- **Multiple Backends** - In-memory, RDF files, and extensible to databases
- **System Graph** - Track Python code semantics, function calls, and execution metadata
- **Decorator-based Annotations** - Easily annotate classes, functions, and Pydantic models
- **Type Safety** - Full type hints and dataclass-based entities

## Architecture

```
kgcore/
├── api/          # High-level KnowledgeGraph API
├── model/        # Graph model implementations (RDF, Property Graphs)
├── backend/      # Storage backends (RDFLib, file-based, etc.)
└── system/       # System Graph for tracking Python code
```

## Examples

See the `examples/` directory for complete examples:
- `core_kg_api.py` - Basic knowledge graph operations
- `system_kg_api.py` - System graph with decorators and Pydantic models

## License

TODO