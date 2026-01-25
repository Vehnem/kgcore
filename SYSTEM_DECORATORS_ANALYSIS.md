# Analysis: Should `system/` and `decorators/` be merged?

## Current Structure

### `system/` folder:
- `recorder.py` - `SystemRecorder` class (core implementation)
- `schema.py` - `SysLabels` (schema definitions)

### `decorators/` folder:
- `class_.py` - `@class_` decorator (uses `SystemRecorder`)
- `event.py` - `@event` decorator (uses `SystemRecorder`)

## Relationship Analysis

### Dependencies:
- `decorators/class_.py` → imports `SystemRecorder` from `system.recorder`
- `decorators/event.py` → imports `SystemRecorder` from `system.recorder`
- Both decorators create their own `SystemRecorder` instance (`_rec`)
- Both use `SysLabels` (indirectly through SystemRecorder)

### Coupling:
- **Tight coupling**: Decorators are thin wrappers around SystemRecorder
- **Single purpose**: All decorators are specifically for system graph tracking
- **No independence**: Decorators don't work without system components

## Arguments FOR Merging

1. **Tight Coupling**
   - Decorators are just convenience wrappers around SystemRecorder
   - They're not independent - they exist solely to use system graph
   - No other decorators that don't use system graph

2. **Single Cohesive Feature**
   - System graph is one feature: tracking Python code semantics
   - Decorators are the user-facing API for that feature
   - Implementation and API belong together for a cohesive feature

3. **Simpler Structure**
   - One place to look for system graph code
   - Easier to understand the feature as a whole
   - Less navigation between folders

4. **Research Library Context**
   - This is a research/teaching library, not a large framework
   - Simpler structure is better for learning
   - Less abstraction layers needed

## Arguments AGAINST Merging

1. **Separation of Concerns**
   - Decorators are user-facing API
   - System is implementation detail
   - Different abstraction levels

2. **Future Extensibility**
   - Might add other decorators that don't use system graph
   - Keeping separate allows for other decorator types

3. **Common Pattern**
   - Many frameworks separate API from implementation
   - Follows convention of separate folders

4. **Import Clarity**
   - `from kgcore.decorators import event` is clearer than `from kgcore.system import event`
   - Decorators are a distinct concept from "system"

## Recommendation: **MERGE** ✅

### Recommended Structure:

```
system/
  __init__.py
  recorder.py      # SystemRecorder (implementation)
  schema.py        # SysLabels (schema)
  decorators.py    # @class_, @event (user-facing API)
```

Or alternatively:

```
system/
  __init__.py
  recorder.py      # SystemRecorder
  schema.py        # SysLabels
  decorators/
    __init__.py
    class_.py      # @class_ decorator
    event.py       # @event decorator
```

### Why Merge:

1. **They're one feature**: System graph tracking is a single cohesive feature
2. **Tight coupling**: Decorators can't exist without system components
3. **Simpler for users**: One import location for system graph features
4. **Research library**: Simpler structure is better for teaching/learning

### Implementation:

1. Move `decorators/class_.py` and `decorators/event.py` into `system/`
2. Option A: Merge into `system/decorators.py` (single file)
3. Option B: Keep as `system/decorators/` subfolder
4. Update all imports
5. Update `__init__.py` files

### Import Changes:

**Before:**
```python
from kgcore.decorators.event import event
from kgcore.decorators.class_ import class_
from kgcore.system.schema import SysLabels
```

**After (Option A - single file):**
```python
from kgcore.system.decorators import event, class_
from kgcore.system.schema import SysLabels
```

**After (Option B - subfolder):**
```python
from kgcore.system.decorators.event import event
from kgcore.system.decorators.class_ import class_
from kgcore.system.schema import SysLabels
```

## Conclusion

**Recommendation: MERGE into `system/decorators/` subfolder**

This keeps:
- Clear separation (decorators as subfolder)
- Single feature location (all system graph code together)
- Easy imports (`from kgcore.system.decorators import ...`)
- Room for growth (can add more decorators easily)

