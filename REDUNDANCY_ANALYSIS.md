# Redundancy Analysis: model/graph.py vs api/cgm.py

## Current Situation

### Three Similar but Different Graph Representations

1. **`model/graph.py`** - Compatibility layer for kgback
   - `Node(id, labels, props)`
   - `Triple(subject, predicate, object, props)`
   - `Literal(value, datatype)`
   - **Purpose**: Compatibility with external kgback package

2. **`api/cgm.py`** - Core Graph Model (CGM) IR
   - `CoreNode(id, labels, properties)`
   - `CoreEdge(id, source, target, label, properties)`
   - `CoreLiteral(value, datatype, language)`
   - `CoreGraph(nodes, edges, metadata)`
   - **Purpose**: Research/teaching IR for bridging RDF and Property Graphs

3. **`model/base.py`** - High-level user API
   - `KGEntity(id, labels, props)`
   - `KGRelation(id, type, source, target, props)`
   - `KGGraph` (interface)
   - **Purpose**: Model-agnostic user-facing API

## Redundancy Issues

### Conceptual Overlap

| Concept | model/graph.py | api/cgm.py | model/base.py |
|---------|---------------|------------|---------------|
| Node | `Node` | `CoreNode` | `KGEntity` |
| Edge/Relation | `Triple` | `CoreEdge` | `KGRelation` |
| Literal | `Literal` | `CoreLiteral` | (in `Props`) |

### Key Differences

1. **`model/graph.py`**:
   - Simple compatibility shim
   - `Triple` is RDF-oriented (subject-predicate-object)
   - Minimal functionality

2. **`api/cgm.py`**:
   - Full IR with graph container (`CoreGraph`)
   - `CoreEdge` is property-graph oriented (source-target-label)
   - Hashable, designed for conversion workflows
   - Research/teaching focus

3. **`model/base.py`**:
   - High-level API interface
   - `KGRelation` uses `type` instead of `label`
   - Part of the main user-facing API

## Recommendations

### Option 1: Remove `model/graph.py` (if kgback not actively used)

**If kgback compatibility is not needed:**
- Remove `model/graph.py`
- Update `model/__init__.py` to remove exports
- Check if anything imports from `model.graph`

**Pros:**
- Eliminates redundancy
- Simplifies codebase
- Clear separation: `model/base.py` for API, `api/cgm.py` for IR

**Cons:**
- Breaks kgback compatibility (if it's used)

### Option 2: Keep but Document Clearly

**If kgback compatibility is needed:**
- Keep `model/graph.py` but add clear documentation
- Mark as "Legacy compatibility layer"
- Consider deprecation notice if planning to remove

**Pros:**
- Maintains compatibility
- No breaking changes

**Cons:**
- Maintains redundancy
- Confusing for new users

### Option 3: Consolidate (Recommended if possible)

**Create adapter/converter:**
- Keep `model/graph.py` minimal
- Make it a thin wrapper that converts to/from `api/cgm.py` or `model/base.py`
- Or make it import from CGM and provide compatibility interface

**Pros:**
- Reduces redundancy
- Maintains compatibility
- Single source of truth

**Cons:**
- Requires refactoring
- May have performance overhead

## Suggested Action Plan

1. **Check kgback usage**: Search codebase for imports of `model.graph`
2. **If unused**: Remove `model/graph.py` (Option 1)
3. **If used**: Implement Option 3 (consolidate via adapters)
4. **Update documentation**: Clearly explain the three layers:
   - `model/base.py` = User API
   - `api/cgm.py` = Research IR
   - `model/graph.py` = Legacy compatibility (if kept)

## Current Usage Check

From grep results:
- `model/graph.py` is exported in `model/__init__.py`
- **No direct imports found in kgcore codebase itself** (only exported in `__init__.py`)
- kgback is referenced in `backend/factory.py` as an external package providing backends
- kgback backends (postgres, sqlite, sparql, neo4j) are optional external dependencies
- `model/graph.py` exists solely for external kgback package compatibility

## Conclusion

**Confirmed**: `model/graph.py` is **redundant for internal use** but may be needed for external kgback compatibility.

### The Three Layers Serve Different Purposes:

1. **`model/base.py`** (KGEntity, KGRelation, KGGraph)
   - **Purpose**: High-level user-facing API
   - **Used by**: All kgcore backends, main API
   - **Status**: ✅ Core, keep

2. **`api/cgm.py`** (CoreNode, CoreEdge, CoreLiteral, CoreGraph)
   - **Purpose**: Research/teaching IR for bridging RDF and Property Graphs
   - **Used by**: Conversion workflows, research examples
   - **Status**: ✅ Core, keep

3. **`model/graph.py`** (Node, Triple, Literal)
   - **Purpose**: External compatibility with kgback package
   - **Used by**: Nothing in kgcore itself (only exported for external use)
   - **Status**: ⚠️ Redundant internally, but may be needed for kgback

## Recommendation

### Short-term (Safe):
1. **Keep `model/graph.py`** but add deprecation notice
2. **Document clearly** that it's only for external kgback compatibility
3. **Update README** to explain the three layers

### Long-term (If kgback not critical):
1. **Check with kgback maintainers** if they still need `model/graph.py`
2. **If not needed**: Remove `model/graph.py` and update `model/__init__.py`
3. **If needed**: Consider making it a thin adapter that uses CGM internally

### Immediate Action:
- Add documentation comment explaining the three layers
- Mark `model/graph.py` as "Legacy compatibility - may be deprecated"

