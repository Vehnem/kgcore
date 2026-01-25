# System Graph

The System Graph tracks Python code semantics, execution, and provenance using the Core Graph Model (CGM). It automatically records function calls, class definitions, and execution metadata.

## Overview

The System Graph provides:
- Automatic tracking of decorated functions and classes
- Execution run recording with metadata
- Integration with Core Graph Model (CGM)
- Optional persistence to RDF files
- Query support for analyzing code execution

## Quick Start

### Basic Usage with Decorators

```python
from kgcore.system.decorators import event, class_
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore

# Create recorder with file persistence
store = FileRDFStore("system_kg.ttl", format="turtle", auto_save=True)
recorder = SystemRecorder(store=store)

# Decorate a class
@class_("DataProcessor", "A class for processing data")
class DataProcessor:
    def __init__(self, name):
        self.name = name
    
    # Decorate a method
    @event("process_item", "Process a single data item")
    def process_item(self, item):
        return f"Processed {item} with {self.name}"

# Use the decorated code
processor = DataProcessor("MyProcessor")
result = processor.process_item("test_data")
# Automatically tracked in system graph!
```

### Accessing the System Graph

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore

store = FileRDFStore("system_kg.ttl", format="turtle")
recorder = SystemRecorder(store=store)

# ... use decorators ...

# Get the CoreGraph
core = recorder.get_graph()
print(f"Tracked {len(core.nodes)} nodes and {len(core.edges)} edges")

# Access nodes
for node_id, node in core.nodes.items():
    print(f"{node_id}: {node.labels}")
    print(f"  Properties: {node.properties}")
```

## Storing and Retrieving Pydantic Models

### Registering Pydantic Models

You can register Pydantic model classes using the decorator or API:

```python
from kgcore.system.decorators import pydantic_model
from kgcore.system import SystemRecorder
from pydantic import BaseModel, Field

# Using decorator
@pydantic_model("A data point model")
class DataPoint(BaseModel):
    """Represents a single data point."""
    x: float = Field(description="X coordinate")
    y: float = Field(description="Y coordinate")
    label: str = Field(description="Data point label")

# Using API
recorder = SystemRecorder()
recorder.register_pydantic_model(DataPoint, description="A data point model")
```

### Storing Pydantic Instances

Store Pydantic model instances in the system graph:

```python
from kgcore.system import SystemRecorder

recorder = SystemRecorder()

# Create an instance
point = DataPoint(x=1.0, y=2.0, label="point1")

# Store it
instance_node = recorder.store_pydantic_instance(
    point,
    instance_id="point1",  # Optional: provide custom ID
    metadata={"source": "manual_entry"}
)

# The instance is now stored with:
# - Serialized JSON data
# - Links to its model class
# - Timestamp
```

### Retrieving Pydantic Instances

Retrieve stored instances:

```python
# Get a specific instance by ID
point = recorder.get_pydantic_instance("point1", DataPoint)
print(point.x, point.y)  # 1.0 2.0

# Find all instances of a model class
instances = recorder.find_pydantic_instances(DataPoint)
for instance_node in instances:
    instance = recorder.get_pydantic_instance(
        instance_node.properties["http://kgcore.org/system/objectId"],
        DataPoint
    )
    print(instance)

# Find all Pydantic instances (any model)
all_instances = recorder.find_pydantic_instances()
```

### Complete Example

```python
from kgcore.system.decorators import pydantic_model
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore
from pydantic import BaseModel

# Setup recorder with persistence
store = FileRDFStore("models.ttl", format="turtle", auto_save=True)
recorder = SystemRecorder(store=store)

# Define and register model
@pydantic_model("User account information")
class User(BaseModel):
    username: str
    email: str
    active: bool = True

# Create and store instances
user1 = User(username="alice", email="alice@example.com")
user2 = User(username="bob", email="bob@example.com", active=False)

recorder.store_pydantic_instance(user1, instance_id="user_alice")
recorder.store_pydantic_instance(user2, instance_id="user_bob")

# Later: retrieve instances
retrieved_user = recorder.get_pydantic_instance("user_alice", User)
print(retrieved_user.username)  # "alice"

# Query all users
all_users = recorder.find_pydantic_instances(User)
print(f"Found {len(all_users)} users")
```

## SystemRecorder API

### Creating a Recorder

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore, InMemoryRDFStore
from kgcore.api.cgm import CoreGraph

# With file persistence
store = FileRDFStore("system.ttl", format="turtle", auto_save=True)
recorder = SystemRecorder(store=store)

# With in-memory storage
memory_store = InMemoryRDFStore()
recorder = SystemRecorder(store=memory_store)

# With existing CoreGraph
core = CoreGraph()
recorder = SystemRecorder(core=core)

# Backward compatibility (also writes to KGGraph)
from kgcore.api import KG
kg = KG()
recorder = SystemRecorder(kg=kg)  # Also writes to old API
```

### Registering Functions

```python
from kgcore.system import SystemRecorder

recorder = SystemRecorder()

# Register a function manually
node = recorder.register_function(
    qualname="my_module.my_function",
    description="Does something useful",
    metadata={"author": "Alice", "version": "1.0"}
)

print(f"Registered function: {node.id}")
```

### Registering Pydantic Models

```python
from kgcore.system import SystemRecorder
from pydantic import BaseModel

recorder = SystemRecorder()

class MyModel(BaseModel):
    field1: str
    field2: int

# Register the model class (captures fields automatically)
node = recorder.register_pydantic_model(
    MyModel,
    description="My custom model",
    metadata={"version": "1.0"}
)

# All fields are automatically registered as attributes
```

### Storing and Retrieving Objects

```python
from kgcore.system import SystemRecorder
from pydantic import BaseModel

recorder = SystemRecorder()

class MyModel(BaseModel):
    value: str

# Store an instance
instance = MyModel(value="test")
instance_node = recorder.store_pydantic_instance(
    instance,
    instance_id="my_instance_1",
    metadata={"source": "test"}
)

# Retrieve the instance
retrieved = recorder.get_pydantic_instance("my_instance_1", MyModel)
print(retrieved.value)  # "test"

# Find all instances
all_instances = recorder.find_pydantic_instances(MyModel)
```

### Tracking Execution Runs

```python
from kgcore.system import SystemRecorder

recorder = SystemRecorder()

# Register function
func_node = recorder.register_function("my_module.foo", "Test function")

# Start a run
run_id = recorder.start_run(
    func_node.id,
    meta={"input": "test_data", "timestamp": "2024-01-01"}
)

# ... execute function ...

# Finish the run
recorder.finish_run(run_id, meta={"result": "success", "duration": 1.5})
```

## Decorators

### @event Decorator

Tracks function execution with automatic run recording.

```python
from kgcore.system.decorators import event

@event("process_data", "Process input data", version="1.0")
def process_data(data):
    return processed_data

# Call the function
result = process_data("input")
# Automatically tracked: function registration + execution run
```

#### Versioning Options

```python
# Explicit version
@event("func1", "Function 1", version="v1.0.0")
def func1():
    pass

# Timestamp-based versioning
@event("func2", "Function 2", auto_version="timestamp")
def func2():
    pass

# Hash-based versioning (changes when function code changes)
@event("func3", "Function 3", auto_version="hash")
def func3():
    pass
```

#### Additional Metadata

```python
@event(
    "analyze_data",
    "Analyze dataset",
    version="2.0",
    author="Alice",
    category="analysis",
    tags=["ml", "data"]
)
def analyze_data(data):
    return analysis_result
```

#### Error Handling

The `@event` decorator automatically tracks errors:

```python
@event("risky_operation", "May fail")
def risky_operation():
    raise ValueError("Something went wrong")

try:
    risky_operation()
except ValueError:
    pass

# Error is recorded in the system graph with error details
```

### @class_ Decorator

Registers a class in the system graph.

```python
from kgcore.system.decorators import class_

@class_("DataProcessor", "Processes data")
class DataProcessor:
    pass

# Class is automatically registered when defined
```

### @pydantic_model Decorator

Registers a Pydantic model class in the system graph and automatically captures its fields.

```python
from kgcore.system.decorators import pydantic_model
from pydantic import BaseModel

@pydantic_model("A user profile model")
class UserProfile(BaseModel):
    """User profile with name and email."""
    name: str
    email: str
    age: int = 0

# Model class and all its fields are automatically registered
```

The decorator automatically:
- Registers the model class
- Captures all field names and types
- Extracts field descriptions from docstrings or Field descriptions
- Stores the model's JSON schema

## System Graph Schema

### Labels

```python
from kgcore.system.schema import SysLabels

# Node labels
SysLabels.CodeObject    # Any code object
SysLabels.Function      # Function/method
SysLabels.Class         # Class definition
SysLabels.Run           # Execution run
SysLabels.PydanticModel # Pydantic model class
SysLabels.PydanticInstance # Pydantic model instance
SysLabels.Attribute     # Class/object attribute

# Relation types
SysLabels.CALLS         # Run calls Function
SysLabels.HAS_VERSION   # Function has version
SysLabels.HAS_ATTRIBUTE # Class/Model has Attribute
SysLabels.HAS_INSTANCE  # Class/Model has Instance
SysLabels.IS_INSTANCE_OF # Instance is instance of Class/Model
```

### Properties

```python
from kgcore.system.schema import SysProperties

# Standard properties
SysProperties.NAME         # Name of code object
SysProperties.DESCRIPTION  # Description
SysProperties.TIMESTAMP    # Timestamp (ISO format)
SysProperties.STATUS       # Status (running, completed, error)
SysProperties.RESULT       # Result (ok, error)
SysProperties.ERROR        # Error message
SysProperties.VERSION      # Version string
SysProperties.QUALNAME     # Qualified name
SysProperties.FIELD_NAME    # Field/attribute name
SysProperties.FIELD_TYPE    # Field/attribute type
SysProperties.FIELD_DESCRIPTION # Field/attribute description
SysProperties.SERIALIZED_DATA # Serialized object data (JSON)
SysProperties.OBJECT_ID    # Unique object instance identifier
```

## Querying the System Graph

### Using SPARQL

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore
from kgcore.api.cgm import RDFBackend

# Setup
store = FileRDFStore("system.ttl", format="turtle")
recorder = SystemRecorder(store=store)

# ... use decorators ...

# Query with SPARQL
backend = RDFBackend(store=store)
query = """
PREFIX sys: <http://kgcore.org/system/>
SELECT ?function ?name ?description
WHERE {
    ?function a sys:Function .
    ?function sys:name ?name .
    OPTIONAL { ?function sys:description ?description }
}
"""

result = backend.query(query)
for row in result:
    print(f"{row['name']}: {row.get('description', 'No description')}")
```

### Querying Runs

```python
# Find all execution runs
query = """
PREFIX sys: <http://kgcore.org/system/>
SELECT ?run ?function ?timestamp ?status
WHERE {
    ?run a sys:Run .
    ?run sys:timestamp ?timestamp .
    ?run sys:status ?status .
    ?run sys:CALLS ?function .
}
ORDER BY DESC(?timestamp)
"""

result = backend.query(query)
for row in result:
    print(f"Run at {row['timestamp']}: {row['status']}")
```

### Finding Errors

```python
# Find failed runs
query = """
PREFIX sys: <http://kgcore.org/system/>
SELECT ?run ?function ?error
WHERE {
    ?run a sys:Run .
    ?run sys:status "error" .
    ?run sys:error ?error .
    ?run sys:CALLS ?function .
}
"""

result = backend.query(query)
for row in result:
    print(f"Error in {row['function']}: {row['error']}")
```

## Saving and Loading

### Save to RDF File

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore

# Auto-save mode
store = FileRDFStore("system.ttl", format="turtle", auto_save=True)
recorder = SystemRecorder(store=store)
# Automatically saves after each operation

# Manual save
store2 = FileRDFStore("system2.ttl", format="turtle", auto_save=False)
recorder2 = SystemRecorder(store=store2)
# ... use recorder ...
recorder2.save_to_rdf()  # Manual save
```

### Load from File

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore
from kgcore.api.cgm import RDFBackend

# Load existing system graph
store = FileRDFStore("system.ttl", format="turtle")
backend = RDFBackend(store=store)
result = backend.to_core(mode="simple")
core = result.graph

# Create recorder with loaded graph
recorder = SystemRecorder(core=core)
```

## Advanced Usage

### Custom Recorder per Module

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore

# Create module-specific recorder
module_store = FileRDFStore("my_module.ttl", format="turtle")
module_recorder = SystemRecorder(store=module_store)

# Override global recorder in decorators
from kgcore.system.decorators.event import _rec
original_rec = _rec
_rec = module_recorder

try:
    # Use decorators - they'll use module_recorder
    @event("module_function", "Module function")
    def module_function():
        pass
finally:
    _rec = original_rec
```

### Combining Multiple Recorders

```python
from kgcore.system import SystemRecorder
from kgcore.api.rdf_store import FileRDFStore

# Create multiple recorders
main_store = FileRDFStore("main.ttl", format="turtle")
main_recorder = SystemRecorder(store=main_store)

debug_store = FileRDFStore("debug.ttl", format="turtle")
debug_recorder = SystemRecorder(store=debug_store)

# Register in both
func_node1 = main_recorder.register_function("func1", "Function 1")
func_node2 = debug_recorder.register_function("func1", "Function 1")
```

## Best Practices

1. **Use file persistence**: Enable `auto_save=True` for automatic persistence.

2. **Version your functions**: Use `auto_version="hash"` to track code changes.

3. **Add metadata**: Include useful metadata (author, category, etc.) in decorators.

4. **Query regularly**: Use SPARQL queries to analyze execution patterns.

5. **Separate concerns**: Use different recorders/files for different modules or projects.

6. **Handle errors**: The decorator automatically tracks errors, but you can add custom error handling.

## See Also

- [Core Graph Model](./core_graph_model.md) - Understanding the underlying IR
- [RDF Backend](./rdf_backend.md) - Converting system graph to RDF
- [Query Support](./query_support.md) - Querying system graph data

