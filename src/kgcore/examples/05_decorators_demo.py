# examples/05_decorators_demo.py
from kgcore.api import KG
from kgcore.decorators.event import event
from kgcore.decorators.class_ import class_
from kgcore.system.schema import SysLabels
import os

# Configuration: Set to True for development/debugging (keeps files)
# Set to False for clean examples (uses temp directory)
USE_PERSISTENT_FILES = True

print("=== KGcore Decorators Demo ===\n")

def run_demo():
    """Run the decorators demo with the configured KG."""
    print("1. Creating decorated functions and classes...")
    
    # Create a decorated class
    @class_("DataProcessor", "A class for processing data")
    class DataProcessor:
        def __init__(self, name):
            self.name = name
            self.processed_count = 0
        
        @event("process_item", "Process a single data item", 
               category="data_processing", version="1.0")
        def process_item(self, item):
            self.processed_count += 1
            return f"Processed {item} with {self.name}"
        
        @event("batch_process", "Process multiple items", 
               category="data_processing", version="1.0")
        def batch_process(self, items):
            results = []
            for item in items:
                results.append(self.process_item(item))
            return results
    
    # Create a utility function
    @event("validate_data", "Validate input data", 
           category="validation", version="2.0", author="kgcore")
    def validate_data(data):
        if not isinstance(data, (list, tuple)):
            raise ValueError("Data must be a list or tuple")
        return len(data) > 0
    
    print("   ✓ Created decorated class and functions")
    
    print("\n2. Using the decorated code...")
    
    # Use the decorated class
    processor = DataProcessor("TestProcessor")
    
    # Process some data
    data = ["item1", "item2", "item3"]
    
    if validate_data(data):
        results = processor.batch_process(data)
        print(f"   ✓ Processed {len(results)} items")
        print(f"   ✓ Results: {results[:2]}...")
    
    print("\n3. System Graph Analysis...")
    
    # Analyze what was recorded in the system graph
    functions = kg.find_entities(SysLabels.Function)
    runs = kg.find_entities(SysLabels.Run)
    relations = kg.find_relations("CALLS")
    
    print(f"   📊 Functions registered: {len(functions)}")
    for func in functions:
        print(f"      - {func.props.get('name', 'Unknown')}: {func.props.get('description', 'No description')}")
    
    print(f"   📊 Function runs recorded: {len(runs)}")
    for run in runs:
        print(f"      - {run.props.get('name', 'Unknown')} at {run.props.get('ts', 'Unknown time')}")
        print(f"        Metadata: {run.props}")
    
    print(f"   📊 CALLS relations: {len(relations)}")
    for rel in relations:
        print(f"      - Run {rel.source} calls Function {rel.target}")
    
    print("\n4. RDF Output (System Graph)...")
    print("   The system graph tracks code provenance and execution:")
    with open(file_path, "r") as f:
        content = f.read()
        # Show first 20 lines to keep output manageable
        lines = content.split('\n')
        for line in lines[:20]:
            print(f"   {line}")
        if len(lines) > 20:
            print(f"   ... ({len(lines) - 20} more lines)")
    
    print("\n5. Key Benefits:")
    print("   ✅ Automatic code provenance tracking")
    print("   ✅ Execution metadata capture")
    print("   ✅ Error handling and logging")
    print("   ✅ Integration with knowledge graph backends")
    print("   ✅ RDF serialization for interoperability")

if USE_PERSISTENT_FILES:
    # Use regular directory for development/debugging
    output_dir = "examples_output"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "decorators_demo.ttl")
    print(f"Using persistent files in: {os.path.abspath(output_dir)}")
    kg = KG(backend="rdf_file", file_path=file_path, format="turtle")
    
    # Override the global system recorders to use our test KG
    from kgcore.decorators.event import _rec as event_rec
    from kgcore.decorators.class_ import _rec as class_rec
    original_event_kg = event_rec.kg
    original_class_kg = class_rec.kg
    event_rec.kg = kg
    class_rec.kg = kg
    
    try:
        run_demo()
    finally:
        # Restore original KGs
        event_rec.kg = original_event_kg
        class_rec.kg = original_class_kg
else:
    # Use temp directory for clean examples
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "decorators_demo.ttl")
        kg = KG(backend="rdf_file", file_path=file_path, format="turtle")
        
        # Override the global system recorders to use our test KG
        from kgcore.decorators.event import _rec as event_rec
        from kgcore.decorators.class_ import _rec as class_rec
        original_event_kg = event_rec.kg
        original_class_kg = class_rec.kg
        event_rec.kg = kg
        class_rec.kg = kg
        
        try:
            run_demo()
        finally:
            # Restore original KGs
            event_rec.kg = original_event_kg
            class_rec.kg = original_class_kg

print("\n🎉 Decorators demo completed!")