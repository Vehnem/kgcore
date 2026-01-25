# RDF Storage

The RDF storage system provides a unified interface for storing and retrieving RDF data, abstracting away the underlying storage mechanism (memory, file, database, etc.).

## Overview

The `RDFStore` interface provides:
- Uniform API for different storage backends
- Automatic persistence (for file-based stores)
- Query interface for triples
- Integration with RDFBackend

## Storage Backends

### InMemoryRDFStore

In-memory storage using rdflib.Graph. Data is lost when the process ends.

```python
from kgcore.api.rdf_store import InMemoryRDFStore
from rdflib import URIRef, Literal, RDF, Namespace

# Create store
store = InMemoryRDFStore()

# Add triples
EX = Namespace("http://example.org/")
alice = URIRef("http://example.org/alice")
store.add_triple(alice, RDF.type, EX.Person)
store.add_triple(alice, EX.name, Literal("Alice"))

# Query triples
all_triples = list(store.triples((None, None, None)))
print(f"Total triples: {len(all_triples)}")

# Query specific pattern
alice_triples = list(store.triples((alice, None, None)))
print(f"Alice triples: {len(alice_triples)}")

# Remove triple
store.remove_triple(alice, EX.name, Literal("Alice"))

# Clear all
store.clear()

# Get underlying graph
graph = store.get_graph()
```

### FileRDFStore

File-based persistence. Automatically loads from and saves to a file.

```python
from kgcore.api.rdf_store import FileRDFStore
from rdflib import URIRef, Literal, RDF, Namespace
from pathlib import Path

# Create store (auto-loads if file exists)
store = FileRDFStore("data.ttl", format="turtle", auto_save=True)

# Add triples (auto-saves if auto_save=True)
EX = Namespace("http://example.org/")
alice = URIRef("http://example.org/alice")
store.add_triple(alice, RDF.type, EX.Person)
store.add_triple(alice, EX.name, Literal("Alice"))
# Automatically saved to file

# Manual save
store.save()

# Load from existing file
store2 = FileRDFStore("data.ttl", format="turtle")
# Data is automatically loaded

# Check file
file_path = Path("data.ttl")
if file_path.exists():
    print(f"File size: {file_path.stat().st_size} bytes")
```

### Auto-Save vs Manual Save

```python
# Auto-save mode (saves after each modification)
store_auto = FileRDFStore("auto.ttl", format="turtle", auto_save=True)
store_auto.add_triple(s, p, o)  # Automatically saved

# Manual save mode
store_manual = FileRDFStore("manual.ttl", format="turtle", auto_save=False)
store_manual.add_triple(s, p, o)
store_manual.add_triple(s2, p2, o2)
store_manual.save()  # Save all at once
```

## Working with RDFBackend

### Using Store with Backend

```python
from kgcore.api.cgm import RDFBackend, CoreGraph, CoreNode
from kgcore.api.rdf_store import FileRDFStore

# Create store and backend
store = FileRDFStore("graph.ttl", format="turtle", auto_save=True)
backend = RDFBackend(store=store)

# Create CoreGraph
core = CoreGraph()
node = CoreNode(id="node1", labels=["Person"], properties={"name": "Alice"})
core.add_node(node)

# Convert and save
backend.from_core(core, mode="simple", target_store=True)
# Automatically saved to file

# Read back
result = backend.to_core(mode="simple")
retrieved = result.graph
```

### Switching Between Stores

```python
from kgcore.api.cgm import RDFBackend
from kgcore.api.rdf_store import InMemoryRDFStore, FileRDFStore

# Start with in-memory
memory_store = InMemoryRDFStore()
backend = RDFBackend(store=memory_store)

# ... work with data ...

# Switch to file storage
file_store = FileRDFStore("backup.ttl", format="turtle")
backend2 = RDFBackend(store=file_store)

# Copy data
core = backend.to_core(mode="simple").graph
backend2.from_core(core, mode="simple", target_store=True)
```

## Triple Operations

### Adding Triples

```python
from kgcore.api.rdf_store import InMemoryRDFStore
from rdflib import URIRef, Literal, RDF, Namespace

store = InMemoryRDFStore()
EX = Namespace("http://example.org/")

# Add single triple
store.add_triple(
    URIRef("http://example.org/alice"),
    RDF.type,
    EX.Person
)

# Add multiple triples
triples = [
    (URIRef("http://example.org/alice"), EX.name, Literal("Alice")),
    (URIRef("http://example.org/alice"), EX.age, Literal(30)),
    (URIRef("http://example.org/bob"), RDF.type, EX.Person),
]

for s, p, o in triples:
    store.add_triple(s, p, o)
```

### Querying Triples

```python
from kgcore.api.rdf_store import InMemoryRDFStore
from rdflib import URIRef, RDF, Namespace

store = InMemoryRDFStore()
# ... add triples ...

# Query all triples
all_triples = list(store.triples((None, None, None)))

# Query by subject
alice = URIRef("http://example.org/alice")
alice_triples = list(store.triples((alice, None, None)))

# Query by predicate
EX = Namespace("http://example.org/")
name_triples = list(store.triples((None, EX.name, None)))

# Query by object
person_triples = list(store.triples((None, None, EX.Person)))

# Query specific pattern
specific = list(store.triples((alice, RDF.type, EX.Person)))
```

### Removing Triples

```python
from kgcore.api.rdf_store import InMemoryRDFStore
from rdflib import URIRef, Literal

store = InMemoryRDFStore()
# ... add triples ...

# Remove specific triple
store.remove_triple(
    URIRef("http://example.org/alice"),
    URIRef("http://example.org/name"),
    Literal("Alice")
)

# Clear all triples
store.clear()
```

## File Formats

FileRDFStore supports various RDF formats:

```python
from kgcore.api.rdf_store import FileRDFStore

# Turtle (default, human-readable)
store_ttl = FileRDFStore("data.ttl", format="turtle")

# N3
store_n3 = FileRDFStore("data.n3", format="n3")

# RDF/XML
store_xml = FileRDFStore("data.rdf", format="xml")

# JSON-LD
store_json = FileRDFStore("data.jsonld", format="json-ld")

# N-Triples
store_nt = FileRDFStore("data.nt", format="nt")
```

## Error Handling

```python
from kgcore.api.rdf_store import FileRDFStore
from pathlib import Path

# Handle non-existent file (starts empty)
store = FileRDFStore("new_file.ttl", format="turtle")
# No error, just empty store

# Handle invalid file format
try:
    store = FileRDFStore("corrupted.ttl", format="turtle")
except Exception as e:
    print(f"Failed to load: {e}")

# Handle save errors
try:
    store.save()
except RuntimeError as e:
    print(f"Failed to save: {e}")
```

## Best Practices

1. **Use auto_save for frequent updates**: Enable `auto_save=True` when making many small changes.

2. **Use manual save for batch operations**: Disable `auto_save` and call `save()` once after batch operations.

3. **Choose appropriate format**: Use `turtle` for human-readable files, `nt` for compact storage.

4. **Handle missing files**: FileRDFStore gracefully handles non-existent files (starts empty).

5. **Check file size**: For large graphs, monitor file size and consider database backends.

6. **Use in-memory for temporary data**: Use `InMemoryRDFStore` for temporary processing.

## Implementation Details

### Store Interface

All stores implement the `RDFStore` interface:

```python
class RDFStore(ABC):
    def add_triple(self, subject, predicate, object) -> None: ...
    def remove_triple(self, subject, predicate, object) -> None: ...
    def triples(self, pattern) -> Iterator: ...
    def __len__(self) -> int: ...
    def clear(self) -> None: ...
    def get_graph(self) -> Graph: ...
    def save(self) -> None: ...  # Optional
    def load(self) -> None: ...   # Optional
```

### Creating Custom Stores

You can implement your own storage backend:

```python
from kgcore.api.rdf_store import RDFStore
from rdflib import Graph

class CustomRDFStore(RDFStore):
    def __init__(self, connection_string: str):
        self._graph = Graph()
        # ... initialize custom storage ...
    
    def add_triple(self, subject, predicate, object) -> None:
        self._graph.add((subject, predicate, object))
        # ... persist to custom storage ...
    
    # Implement other required methods...
```

## See Also

- [RDF Backend](./rdf_backend.md) - Using stores with RDFBackend
- [Core Graph Model](./core_graph_model.md) - Converting to/from CoreGraph
- [Query Support](./query_support.md) - Querying stored data

