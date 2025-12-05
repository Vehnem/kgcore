# Query Support

kgcore provides query interfaces for different graph backends, with standardized result formats.

## Overview

- **SPARQL** for RDF backends (implemented)
- **Cypher** for Property Graph backends (planned)
- Standardized `QueryResult` format across all backends

## SPARQL Queries

### Basic SELECT Query

```python
from kgcore.api.cgm import RDFBackend
from kgcore.api.rdf_store import InMemoryRDFStore
from kgcore.api.cgm import CoreGraph, CoreNode, CoreEdge

# Setup: Create graph and store
store = InMemoryRDFStore()
backend = RDFBackend(store=store)

# Load data
core = CoreGraph()
alice = CoreNode(
    id="http://example.org/alice",
    labels=["http://example.org/Person"],
    properties={
        "http://example.org/name": "Alice",
        "http://example.org/age": 30
    }
)
bob = CoreNode(
    id="http://example.org/bob",
    labels=["http://example.org/Person"],
    properties={
        "http://example.org/name": "Bob",
        "http://example.org/age": 25
    }
)
core.add_node(alice)
core.add_node(bob)
core.add_edge(CoreEdge(
    id="e1",
    source="http://example.org/alice",
    target="http://example.org/bob",
    label="http://example.org/knows"
))

backend.from_core(core, mode="simple", target_store=True)

# Query
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
```

### Filtering and Conditions

```python
# Filter by age
query = """
PREFIX ex: <http://example.org/>
SELECT ?person ?name
WHERE {
    ?person a ex:Person .
    ?person ex:name ?name .
    ?person ex:age ?age .
    FILTER (?age > 25)
}
"""

result = backend.query(query)
```

### Relationship Queries

```python
# Find who knows whom
query = """
PREFIX ex: <http://example.org/>
SELECT ?person1 ?person2
WHERE {
    ?person1 ex:knows ?person2 .
}
"""

result = backend.query(query)
for row in result:
    print(f"{row['person1']} knows {row['person2']}")
```

### Aggregate Queries

```python
# Count persons
query = """
PREFIX ex: <http://example.org/>
SELECT (COUNT(?person) as ?count)
WHERE {
    ?person a ex:Person .
}
"""

result = backend.query(query)
count = result.rows[0]["count"]
print(f"Total persons: {count}")
```

### Complex Queries

```python
# Find persons and their relationships
query = """
PREFIX ex: <http://example.org/>
SELECT ?person ?name ?friend
WHERE {
    ?person a ex:Person .
    ?person ex:name ?name .
    OPTIONAL {
        ?person ex:knows ?friend .
    }
}
ORDER BY ?name
"""

result = backend.query(query)
```

## QueryResult API

### Accessing Results

```python
from kgcore.api.query import QueryResult

# Get number of results
count = len(result)

# Iterate over results
for row in result:
    print(row)

# Get as list
rows = result.to_list()

# Get as dictionary (keyed by column)
by_person = result.to_dict("person")
alice_data = by_person.get("http://example.org/alice")
```

### Result Metadata

```python
# Query information
print(f"Query type: {result.query_type}")  # 'sparql'
print(f"Query string: {result.query_string}")
print(f"Columns: {result.columns}")  # ['person', 'name', 'age']

# Additional metadata
print(f"Metadata: {result.metadata}")
# May include: result_type, vars, error, etc.
```

### Error Handling

```python
# Check for errors
result = backend.query("INVALID QUERY")

if "error" in result.metadata:
    print(f"Error: {result.metadata['error']}")
    print(f"Error type: {result.metadata.get('error_type')}")
else:
    # Process results
    for row in result:
        print(row)
```

## Query Without Store

If you need to query without a persistent store:

```python
from kgcore.api.cgm import RDFBackend
from rdflib import Graph, URIRef, Literal, RDF, Namespace

# Create RDF graph directly
rdf_graph = Graph()
EX = Namespace("http://example.org/")
alice = URIRef("http://example.org/alice")
rdf_graph.add((alice, RDF.type, EX.Person))
rdf_graph.add((alice, EX.name, Literal("Alice")))

# Convert to CoreGraph first
backend = RDFBackend()
core_result = backend.to_core(rdf_graph, mode="simple")

# Then use store for querying
from kgcore.api.rdf_store import InMemoryRDFStore
store = InMemoryRDFStore()
backend_with_store = RDFBackend(store=store)
backend_with_store.from_core(core_result.graph, mode="simple", target_store=True)

# Now can query
result = backend_with_store.query("SELECT ?s WHERE { ?s ?p ?o }")
```

## Supported Query Types

```python
from kgcore.api.cgm import RDFBackend

backend = RDFBackend(store=store)
supported = backend.get_supported_query_types()
print(supported)  # ['sparql']
```

## Property Graph Queries (Planned)

Cypher support is planned for Property Graph backends:

```python
from kgcore.api.cgm import PropertyGraphBackend

# This will be available in the future
backend = PropertyGraphBackend()
query = "MATCH (p:Person) RETURN p.name"
result = backend.query(query, query_type="cypher")
```

## Best Practices

1. **Use parameterized queries**: For user input, use SPARQL parameter binding to prevent injection.

2. **Check for errors**: Always check `result.metadata` for errors before processing results.

3. **Handle optional values**: Use `row.get('column', default)` for optional columns.

4. **Use appropriate queries**: For simple lookups, consider using CoreGraph methods instead of SPARQL.

5. **Cache results**: For expensive queries, consider caching QueryResult objects.

6. **Monitor performance**: Large queries may be slow; consider pagination or limiting results.

## Example: Complete Query Workflow

```python
from kgcore.api.cgm import RDFBackend, CoreGraph, CoreNode
from kgcore.api.rdf_store import FileRDFStore

# Setup persistent store
store = FileRDFStore("knowledge_base.ttl", format="turtle", auto_save=True)
backend = RDFBackend(store=store)

# Load or create data
# ... populate CoreGraph and convert ...

# Query for specific information
query = """
PREFIX ex: <http://example.org/>
SELECT ?person ?name ?age
WHERE {
    ?person a ex:Person .
    ?person ex:name ?name .
    OPTIONAL { ?person ex:age ?age }
}
ORDER BY ?name
"""

result = backend.query(query)

# Process results
if "error" in result.metadata:
    print(f"Query failed: {result.metadata['error']}")
else:
    print(f"Found {len(result)} persons:")
    for row in result:
        name = row['name']
        age = row.get('age', 'unknown')
        print(f"  {name} (age: {age})")
    
    # Convert to dictionary for easy lookup
    by_name = {row['name']: row for row in result}
    if 'Alice' in by_name:
        print(f"Alice's data: {by_name['Alice']}")
```

## See Also

- [RDF Backend](./rdf_backend.md) - Using queries with RDFBackend
- [RDF Storage](./rdf_storage.md) - Setting up stores for querying
- [Core Graph Model](./core_graph_model.md) - Understanding the data model

