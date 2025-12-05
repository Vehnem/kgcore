# Recommended Code Structure for KGcore

## Analysis

### Current State
- **High-level API**: `model/` (KGGraph, KGEntity, KGRelation) - user-facing API
- **Core Graph Model (CGM)**: `api/cgm.py` - research/teaching IR for bridging RDF/PGM
- **Backends**: `backend/` - implementations of KGGraph interface
- **System Graph**: `system/` - Python code tracking
- **Decorators**: `decorators/` - system graph annotations
- **Storage**: `api/rdf_store.py` - storage abstraction
- **Query**: `api/query.py` - query interfaces
- **Serialization**: `serialization/` - JSON-LD export

### README Structure vs Reality
The README mentions:
- `api/sys.py` → We have `system/recorder.py` and `system/schema.py`
- `api/decorators.py` → We have `decorators/class_.py` and `decorators/event.py`
- `api/model.py` → We have `model/base.py`, `model/graph.py`, `model/ontology.py`
- `io/` → We have `serialization/jsonld.py`

## Recommended Structure

```
src/kgcore/
├── __init__.py                 # Main exports (KG factory, etc.)
├── api.py                      # Main KG() factory function (keep as-is)
├── cli.py                      # CLI interface
├── config.py                   # Configuration management
│
├── model/                       # High-level model-agnostic API
│   ├── __init__.py
│   ├── base.py                 # KGGraph, KGEntity, KGRelation (core API)
│   ├── graph.py                # Graph utilities (Triple, Node, Literal)
│   └── ontology.py             # Ontology management
│
├── core/                       # Core Graph Model (CGM) - Research/Teaching IR
│   ├── __init__.py             # Export CGM classes
│   ├── ir.py                   # Core IR: CoreGraph, CoreNode, CoreEdge, CoreLiteral
│   ├── adapters.py             # GraphBackend, RDFBackend, PropertyGraphBackend
│   ├── modes.py                # Conversion modes registry
│   ├── query.py                # Query interfaces (QueryResult, QueryType)
│   └── storage/                # Storage abstractions
│       ├── __init__.py
│       ├── base.py              # RDFStore abstract interface
│       ├── memory.py            # InMemoryRDFStore
│       └── file.py              # FileRDFStore
│
├── backend/                    # Backend implementations (KGGraph interface)
│   ├── __init__.py
│   ├── factory.py              # Backend factory
│   ├── memory.py               # InMemoryGraph (implements KGGraph)
│   ├── rdf_rdflib.py           # RDFLibGraph (implements KGGraph)
│   └── rdf_file.py             # RDFFileGraph (implements KGGraph)
│
├── system/                      # System Graph (Python code tracking)
│   ├── __init__.py
│   ├── recorder.py             # SystemRecorder
│   └── schema.py               # SysLabels, system graph schema
│
├── decorators/                  # Decorators for system graph
│   ├── __init__.py
│   ├── class_.py               # @class_ decorator
│   └── event.py                # @event decorator
│
├── serialization/               # Serialization/Export (was "io")
│   ├── __init__.py
│   └── jsonld.py               # JSON-LD serialization
│
└── common/                      # Shared utilities
    ├── __init__.py
    ├── types.py                # Common types (KGId, Props, Lit, Result)
    └── errors.py               # Error classes
```

## Key Changes Explained

### 1. Rename `api/` → `core/`
**Rationale**: 
- The current `api/` folder contains the Core Graph Model (CGM), which is a research/teaching IR, not the main user API
- The main user API is in `model/` (KGGraph interface)
- `core/` better reflects that this is the core IR for bridging different graph models

**Files to move**:
- `api/cgm.py` → `core/ir.py` (CoreGraph IR classes)
- `api/cgm.py` (RDFBackend, etc.) → `core/adapters.py` (split adapters from IR)
- `api/modes.py` → `core/modes.py`
- `api/query.py` → `core/query.py`
- `api/rdf_store.py` → `core/storage/base.py`, `core/storage/memory.py`, `core/storage/file.py`

### 2. Keep `model/` as High-Level API
**Rationale**:
- `model/` contains the user-facing API (KGGraph, KGEntity, KGRelation)
- This is the model-agnostic interface mentioned in the README
- Backends implement this interface

### 3. Keep `backend/` for KGGraph Implementations
**Rationale**:
- Backends implement the `KGGraph` interface from `model/base.py`
- These are concrete implementations (memory, rdf_file, etc.)
- Factory pattern for creating backends

### 4. Rename `serialization/` → Keep as-is (or document as "io")
**Rationale**:
- README mentions `io/` but we have `serialization/`
- Either rename to `io/` or update README
- Suggestion: Keep `serialization/` (more descriptive) and update README

### 5. System Graph Stays in `system/`
**Rationale**:
- Clear separation of concerns
- System graph is a feature, not core infrastructure
- Decorators stay separate as they use system graph

## Import Structure

### User-facing (High-level API)
```python
from kgcore.api import KG  # Factory function
from kgcore.model import KGGraph, KGEntity, KGRelation  # Main API
```

### Core Graph Model (Research/Teaching)
```python
from kgcore.core import CoreGraph, CoreNode, CoreEdge  # IR classes
from kgcore.core import RDFBackend, PropertyGraphBackend  # Adapters
from kgcore.core.storage import InMemoryRDFStore, FileRDFStore  # Storage
from kgcore.core.query import QueryResult  # Query results
```

### System Graph
```python
from kgcore.system import SystemRecorder
from kgcore.decorators import class_, event
```

## Migration Path

1. **Phase 1**: Create new `core/` structure alongside existing `api/`
2. **Phase 2**: Move files from `api/` to `core/`
3. **Phase 3**: Update all imports
4. **Phase 4**: Remove old `api/` folder (except `api.py`)
5. **Phase 5**: Update README to reflect new structure

## Updated README Structure Section

```markdown
## Structure

```
src/kgcore/
  api.py              # Main KG() factory
  model/              # High-level model-agnostic API (KGGraph, KGEntity, KGRelation)
  core/               # Core Graph Model (CGM) - IR for bridging RDF/PGM
    ir.py            # Core IR classes
    adapters.py      # RDFBackend, PropertyGraphBackend
    modes.py         # Conversion modes
    query.py         # Query interfaces
    storage/         # Storage abstractions
  backend/            # Backend implementations (memory, rdf_file, etc.)
  system/             # System Graph (Python code tracking)
  decorators/         # @class_, @event decorators
  serialization/      # JSON-LD export
  common/             # Shared types and utilities
```
```

