# Changelog - Core Graph Model Implementation Session

## Major Features Added

### Core Graph Model (CGM) - Research/Teaching IR
- **Added** `kgcore.api.cgm` module with Core Graph Model intermediate representation
  - `CoreNode` - Nodes with id, labels, and properties
  - `CoreEdge` - Edges with id, source, target, label, and properties
  - `CoreLiteral` - Typed literals with value, datatype, and language tag
  - `CoreGraph` - Graph container with nodes, edges, and metadata
- **Added** `GraphBackend` abstract base class for graph adapters
- **Added** `RDFBackend` adapter for RDF graphs with multiple conversion modes
- **Added** `PropertyGraphBackend` placeholder for property graph adapters
- **Added** `ConversionResult` class with warnings and metadata tracking

### Conversion Modes System
- **Added** `kgcore.api.modes` module with conversion mode registry
  - Mode documentation with `preserves`, `loses`, and `warnings` information
  - RDF to CoreGraph modes: `simple`, `reified_edges`, `quads_with_context`
  - CoreGraph to RDF modes: `simple`, `edge_properties_as_reification`
  - Property Graph modes: `simple`, `rdf_labels_as_node_labels`, `rdf_type_as_property`
- **Added** `get_mode_info()` and `list_modes()` utilities

### RDF Storage Abstraction
- **Added** `kgcore.api.rdf_store` module with storage interface
  - `RDFStore` abstract base class for storage backends
  - `InMemoryRDFStore` - In-memory storage using rdflib.Graph
  - `FileRDFStore` - File-based persistence with auto-save option
  - `DatabaseRDFStore` - Placeholder for future database backends
- **Refactored** `RDFBackend` to use `RDFStore` interface instead of direct rdflib.Graph
- **Added** backward compatibility: RDFBackend still works with rdflib.Graph directly

### Query Support
- **Added** `kgcore.api.query` module with query interfaces
  - `QueryResult` class with standardized result format
  - `QueryType` enum for supported query types
  - `QueryError` class for error handling
- **Implemented** SPARQL query support in `RDFBackend`
  - `query()` method for executing SPARQL queries
  - Converts rdflib results to standardized `QueryResult` format
  - Error handling with informative messages
- **Added** `get_supported_query_types()` method to backends
- **Added** Cypher query placeholder in `PropertyGraphBackend`

### System Graph Refactoring
- **Refactored** `SystemRecorder` to use CoreGraph IR instead of KGGraph API
  - Now uses `CoreGraph`, `CoreNode`, `CoreEdge` internally
  - Optional `RDFStore` for persistence
  - Backward compatibility: optional `kg` parameter for old KGGraph API
- **Updated** `SysLabels` to use URIs (e.g., `"http://kgcore.org/system/Function"`)
- **Added** `SysProperties` class for standard property names
- **Moved** decorators from `kgcore.decorators/` to `kgcore.system/decorators/`
  - `@class_` decorator now in `system/decorators/class_.py`
  - `@event` decorator now in `system/decorators/event.py`
- **Added** backward compatibility redirects in old `decorators/` folder

### Model and Common Types Updates
- **Updated** `kgcore.common.types` with CGM alignment
  - Added documentation explaining relationship with CoreGraph Model
  - Added conversion utilities: `lit_to_core_literal()`, `core_literal_to_lit()`
  - Clarified `Lit` vs `CoreLiteral` differences
- **Updated** `kgcore.model.base` with comprehensive documentation
  - Clarified two graph models: High-level API vs Core Graph Model
  - Made `KGGraph` an abstract base class with proper docstrings
  - Documented differences between `KGRelation.type` and `CoreEdge.label`
- **Added** `kgcore.model.converters` module
  - Conversion utilities between high-level API and CGM
  - `kg_entity_to_core_node()` / `core_node_to_kg_entity()`
  - `kg_relation_to_core_edge()` / `core_edge_to_kg_relation()`
  - `kg_graph_to_core_graph()` / `core_graph_to_kg_graph()`
- **Updated** `kgcore.model.__init__.py` with clear documentation and converter exports

## Testing and Examples

- **Converted** examples to comprehensive unit tests
  - `test_cgm.py` - Tests for Core IR classes
  - `test_rdf_backend.py` - RDF conversion and round-trip tests
  - `test_rdf_store.py` - Storage backend tests
  - `test_query.py` - Query functionality tests
- **Simplified** `07_core_graph_model.py` example to minimal demo

## Documentation

- **Updated** `README.md` with comprehensive documentation
  - Added Installation section
  - Added Quick Start with multiple examples
  - Expanded Features list
  - Updated Structure section to reflect actual codebase
  - Added Examples, Testing, and Contributing sections
- **Created** `STRUCTURE_PROPOSAL.md` - Detailed architecture analysis
- **Created** `REDUNDANCY_ANALYSIS.md` - Analysis of model/graph.py vs api/cgm.py
- **Created** `SYSTEM_DECORATORS_ANALYSIS.md` - Analysis of system/decorators merge

## Code Organization

- **Reorganized** system graph code
  - All system graph code now in `system/` folder
  - Decorators moved to `system/decorators/` subfolder
  - Clear separation of concerns
- **Clarified** two graph model architecture
  - High-level API (`model/`) - User-facing, for backends
  - Core Graph Model (`api/cgm`) - Research/teaching IR for conversions
- **Added** conversion utilities between the two models

## API Changes

### New Exports
- `kgcore.api.cgm` - Core Graph Model classes
- `kgcore.api.rdf_store` - Storage interfaces
- `kgcore.api.query` - Query interfaces
- `kgcore.api.modes` - Conversion mode registry
- `kgcore.system.decorators` - System graph decorators
- `kgcore.model.converters` - Conversion utilities

### Backward Compatibility
- Old `kgcore.decorators` imports still work (redirects to new location)
- `RDFBackend` still works with rdflib.Graph directly (no store required)
- `SystemRecorder` supports optional `kg` parameter for old KGGraph API
- All existing backend implementations continue to work

## Files Created

- `src/kgcore/api/cgm.py` - Core Graph Model IR and adapters
- `src/kgcore/api/modes.py` - Conversion mode registry
- `src/kgcore/api/query.py` - Query interfaces
- `src/kgcore/api/rdf_store.py` - Storage abstractions
- `src/kgcore/api/__init__.py` - API exports
- `src/kgcore/system/decorators/__init__.py` - Decorator exports
- `src/kgcore/system/decorators/class_.py` - @class_ decorator
- `src/kgcore/system/decorators/event.py` - @event decorator
- `src/kgcore/model/converters.py` - Conversion utilities
- `src/kgcore/tests/test_cgm.py` - CGM unit tests
- `src/kgcore/tests/test_rdf_backend.py` - RDF backend tests
- `src/kgcore/tests/test_rdf_store.py` - Storage tests
- `src/kgcore/tests/test_query.py` - Query tests
- `STRUCTURE_PROPOSAL.md` - Architecture documentation
- `REDUNDANCY_ANALYSIS.md` - Redundancy analysis
- `SYSTEM_DECORATORS_ANALYSIS.md` - System/decorators analysis

## Files Modified

- `src/kgcore/system/recorder.py` - Refactored to use CoreGraph IR
- `src/kgcore/system/schema.py` - Updated with URIs and SysProperties
- `src/kgcore/system/__init__.py` - Updated exports
- `src/kgcore/common/types.py` - Added CGM alignment and converters
- `src/kgcore/common/__init__.py` - Updated exports
- `src/kgcore/model/base.py` - Added comprehensive documentation
- `src/kgcore/model/__init__.py` - Updated with converters and docs
- `src/kgcore/decorators/` - Converted to backward compatibility redirects
- `src/kgcore/examples/07_core_graph_model.py` - Simplified to minimal demo
- `README.md` - Comprehensive updates

## Architecture Improvements

- **Separation of Concerns**: Clear distinction between high-level API and research IR
- **Storage Abstraction**: RDF storage separated from conversion logic
- **Query Interface**: Standardized query interface across backends
- **Mode System**: Explicit conversion modes with documentation
- **Information Loss Tracking**: Warnings and metadata in conversion results
- **Research Focus**: CoreGraph designed for teaching and exploring tradeoffs

## Breaking Changes

None - All changes maintain backward compatibility through redirects and optional parameters.

