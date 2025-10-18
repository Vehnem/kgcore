# KGcore (Python)

**KGcore** provides a unified Python API for working with diverse **Knowledge Graph (KG)** models — such as RDF and Property Graphs (PGM) — through abstract interfaces.
It enables consistent creation, querying, and manipulation of knowledge graph data, independent of the underlying model or backend.

## Core Idea

* Define a **model-agnostic API** for entities, relations, and metadata.
* Support **RDF** (triples, named graphs, literals) and **PGM** (nodes, edges, properties).
* Provide a **System Graph** to describe Python code — capturing provenance, lineage, evaluation metrics, and semantic annotations of functions, classes, and pipelines.

## Features

* **Abstract Interfaces** for RDF and PGM models
* **Extensible Backends** via adapters (e.g. `rdflib`, SPARQL endpoints, Neo4j)
* **System Graph Integration** for tracking code-level semantics and provenance
* **Decorator-based Annotations** to semantically enrich Python classes and functions
* **JSON-LD Generation** from Pydantic models or Python structures

## Example Usage

```python
@kg.class_(label="Experiment", description="A recorded experiment")
class Experiment:
    pass

@kg.event(name="Run Evaluation", description="Executes model scoring")
def evaluate_model():
    ...
```

```python
from pydantic import BaseModel

class Example(BaseModel):
    id: str
    value: float

kg.add(Example(id="x1", value=0.9))  # Converts to JSON-LD
```

## Meta Concepts

* RDF Reification, Named Graphs, Singleton Properties, N-ary Relations, RDF-Star
* Key–value meta attachments on triples or properties

```python
Triple.addMeta({"confidence": 0.9, "source": "system"})
```

## Persistence

KGcore focuses on the API and data model abstraction.
Persistence and query execution are handled by separate backend modules.

