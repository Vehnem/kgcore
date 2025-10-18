# LLM Context for KGcore Development

This file tells any AI assistant how to reason and code inside this repository.

---

## 🧩 Project Summary

**KGcore** is a lightweight Python library that provides a unified API for manipulating **Knowledge Graphs** (KGs).  
It abstracts over RDF and Property Graph models, and offers:

- Core model primitives (entities, relations, literals)
- Backend adapters (in-memory, RDF with rdflib, RDF file persistence)
- System Graph for tracking Python code provenance (decorators with versioning)
- RDF reification for metadata storage
- Simple ontology layer (`ontology.py`)
- JSON-LD serialization utilities

Goal: **minimal, clean, extensible, and readable** foundation — not a full-featured framework.

---

## 🧭 Design Principles

1. **Keep it minimal.**  
   Implement only what’s needed for clarity and working examples. Avoid unnecessary abstraction layers.

2. **Stay model-agnostic.**  
   API should not depend on RDF or PGM specifics. Those live in adapters.

3. **Strong typing.**  
   Use `dataclasses` and full type hints. Avoid `Any` except for props.

4. **Prefer composition over inheritance.**  
   Use small interfaces + adapter patterns, not deep class hierarchies.

5. **Readable first.**  
   Code should be self-explanatory with 1–2 line docstrings. Avoid verbose comments.

6. **Extensible surface.**  
   Leave clear placeholders / TODOs for:
   - SPARQL querying
   - Neo4j adapter
   - Provenance standards (W3C PROV)
   - Advanced ontology reasoning

---

## 🛠️ Implementation Targets

Core packages:
kgcore/
├── api.py # Facade/factory for KG backends (memory, rdf_file)
├── model/base.py # Abstract model interfaces
├── backend/memory.py # In-memory reference backend
├── backend/rdf_rdflib.py # RDF adapter with reification
├── backend/rdf_file.py # RDF file persistence backend
├── decorators/ # @class_, @event (with versioning)
├── system/ # System graph recorder
├── serialize/jsonld.py # JSON-LD export utilities
├── ontology.py # Ontology API (classes, predicates)
├── common/ # Shared types, errors, helpers
└── tests/ + examples/

## 🧠 LLM Coding Behavior

When generating or editing code:
- ✅ Be concise, deterministic, and directly executable.  
- ✅ Follow the patterns already used in the repo (dataclasses, explicit imports, typed dicts).  
- ✅ Write docstrings, not comments.  
- ✅ Leave `# TODO:` for placeholders, not half-coded functions.  
- ✅ Prefer small pure functions over monolithic ones.  
- 🚫 Do not overarchitect (no DI containers, registries, or metaclasses).  
- 🚫 Do not generate large auto-docs or long explanations in code.

---

## 🧩 Testing & Examples

All features should be demonstrated via:
- `examples/` scripts (human-readable)
- `tests/` with pytest, covering happy paths + edge cases

Each public API addition must have a minimal test and example.

### Current Examples
- `01_minimal_inmemory.py`: Basic KG operations with in-memory backend
- `02_rdf_file_persistence.py`: RDF file persistence demonstration
- `03_rdf_reification.py`: RDF reification for metadata storage
- `04_reification_demo.py`: Comprehensive reification vs regular properties
- `05_decorators_demo.py`: System graph and decorator functionality
- `06_versioning_demo.py`: Versioning strategies and change detection

### Test Coverage
- `test_meta.py`: Decorator functionality and system graph
- `test_reification.py`: RDF reification implementation
- `test_rdf_file.py`: File persistence backend
- `test_versioning.py`: Versioning system and change detection

---

## 📈 Milestone 0.1 Goals

- ✅ InMemoryGraph works end-to-end.  
- ✅ RDF adapter (rdflib) supports create/read with reification.  
- ✅ RDF file persistence backend with auto-save.  
- ✅ Decorators write to the System Graph with versioning.  
- ✅ RDF reification for metadata storage.  
- ✅ Function hash-based change detection.  
- ✅ Timestamp and hash versioning strategies.  
- 🔄 JSON-LD export works from entities and Pydantic models.  
- 🔄 Ontology API validates domain/range.  

Everything else (SPARQL, Neo4j, full meta models) comes later.

---

## 🚀 Implemented Features

### Backend Adapters
- **InMemoryGraph**: Fast in-memory knowledge graph with full CRUD operations
- **RDFLibGraph**: RDF adapter with reification support for metadata storage
- **RDFFileGraph**: Persistent RDF storage with auto-save and multiple formats (Turtle, RDF/XML, JSON-LD)

### Decorators & System Graph
- **@event**: Function execution tracking with automatic versioning
  - Timestamp versioning (`auto_version="timestamp"`)
  - Hash versioning (`auto_version="hash"`) with joblib-inspired change detection
  - Explicit versioning (`version="v1.2.3"`)
- **@class_**: Class registration in system graph
- **System Graph**: Automatic code provenance tracking with RDF serialization

### RDF Features
- **Reification**: Standard RDF reification for metadata about statements
- **File Persistence**: Auto-save to RDF files with configurable formats
- **Metadata Storage**: Rich metadata capture with reified statements
- **Query Support**: Entity and relation finding with property filtering

### Versioning System
- **Function Hashing**: SHA-256 based change detection using source code analysis
- **Timestamp Versions**: `YYYYMMDD_HHMMSS` format for deployment tracking
- **Hash Versions**: 16-character hex hashes for change detection
- **Explicit Versions**: User-defined semantic versions

## 💡 Usage Patterns

### Basic Knowledge Graph
```python
from kgcore.api import KG

# In-memory graph
kg = KG(backend="memory")
entity = kg.create_entity(["Person"], {"name": "Alice"})

# RDF file persistence
kg = KG(backend="rdf_file", file_path="data.ttl", format="turtle")
```

### Decorator Usage
```python
from kgcore.decorators.event import event

# Timestamp versioning
@event("process_data", auto_version="timestamp")
def process_data(x):
    return x * 2

# Hash versioning (detects changes)
@event("analyze", auto_version="hash")
def analyze(data):
    return sum(data)

# Explicit versioning
@event("export", version="v1.2.0")
def export_results():
    return "exported"
```

### RDF Reification
```python
# Add metadata to statements
kg.add_meta(entity.id, {"confidence": 0.95, "source": "manual"})
```

---

## 🗣️ Style Commands for AI (when prompted)

When you, the AI, are asked to:
- *"Add X"* → Implement it minimally, matching structure and tone.  
- *"Extend Y"* → Preserve backward compatibility.  
- *"Refactor Z"* → Keep interfaces stable and simple.  
- *"Explain A"* → Respond briefly, focusing on decisions, not theory.

---

## ✅ Done Means

- Code runs without errors on Python 3.12+.  
- All examples and tests pass.  
- `ruff`, `black`, and `mypy` pass without warnings.  
- No needless complexity added.

---

**Remember:** KGcore is a *clean foundation*, not a feature race.  
Future developers (or AIs) should immediately understand its intent.
