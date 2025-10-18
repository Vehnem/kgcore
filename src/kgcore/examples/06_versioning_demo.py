# examples/06_versioning_demo.py
from kgcore.api import KG
from kgcore.decorators.event import event, _compute_function_hash, _get_timestamp_version
from kgcore.system.schema import SysLabels
import os
import time

# Configuration: Set to True for development/debugging (keeps files)
# Set to False for clean examples (uses temp directory)
USE_PERSISTENT_FILES = True

print("=== KGcore Versioning Demo ===\n")

def run_demo():
    """Run the versioning demo with the configured KG."""
    print("1. Timestamp-based Versioning")
    print("   Automatically generates versions like: 20241018_143022")
    
    @event("timestamped_func", "Function with timestamp versioning", 
           auto_version="timestamp", category="demo")
    def timestamped_func(x):
        return x * 2
    
    # Call the function
    result1 = timestamped_func(5)
    print(f"   ✓ Called timestamped_func(5) = {result1}")
    
    # Wait a moment and call again to show different timestamps
    time.sleep(1.1)
    result2 = timestamped_func(10)
    print(f"   ✓ Called timestamped_func(10) = {result2}")
    
    print("\n2. Hash-based Versioning")
    print("   Automatically generates versions based on function content")
    
    @event("hashed_func", "Function with hash versioning", 
           auto_version="hash", category="demo")
    def hashed_func(x, y=10):
        return x + y
    
    result3 = hashed_func(5)
    print(f"   ✓ Called hashed_func(5) = {result3}")
    
    # Show the hash for this function
    func_hash = _compute_function_hash(hashed_func)
    print(f"   ✓ Function hash: {func_hash}")
    
    print("\n3. Explicit Version Override")
    print("   Manual version overrides automatic versioning")
    
    @event("explicit_func", "Function with explicit version", 
           version="v1.2.3", auto_version="hash", category="demo")
    def explicit_func():
        return "explicit version"
    
    result4 = explicit_func()
    print(f"   ✓ Called explicit_func() = {result4}")
    
    print("\n4. No Versioning")
    print("   Functions without versioning don't get automatic versions")
    
    @event("no_version_func", "Function without versioning", category="demo")
    def no_version_func():
        return "no version"
    
    result5 = no_version_func()
    print(f"   ✓ Called no_version_func() = {result5}")
    
    print("\n5. Hash Change Detection")
    print("   Hash changes when function content changes")
    
    # Create a function and get its hash
    def original_function(x):
        return x + 1
    
    def modified_function(x):
        return x + 2  # Changed the constant
    
    hash_original = _compute_function_hash(original_function)
    hash_modified = _compute_function_hash(modified_function)
    
    print(f"   ✓ Original function hash: {hash_original}")
    print(f"   ✓ Modified function hash: {hash_modified}")
    print(f"   ✓ Hashes are different: {hash_original != hash_modified}")
    
    print("\n6. System Graph Analysis")
    print("   All versions are stored in the knowledge graph")
    
    # Analyze what was recorded
    runs = kg.find_entities(SysLabels.Run)
    print(f"   📊 Total runs recorded: {len(runs)}")
    
    for i, run in enumerate(runs, 1):
        name = run.props.get("name", "Unknown")
        version = run.props.get("version", "No version")
        category = run.props.get("category", "No category")
        print(f"      {i}. {name} (version: {version}, category: {category})")
    
    print("\n7. Version Types Summary")
    print("   📝 Timestamp versions: YYYYMMDD_HHMMSS format")
    print("   🔗 Hash versions: 16-character SHA-256 hash")
    print("   📌 Explicit versions: User-specified strings")
    print("   ❌ No version: When no versioning is specified")
    
    print("\n8. Use Cases")
    print("   🕒 Timestamp versioning: Good for tracking when code was deployed")
    print("   🔍 Hash versioning: Good for detecting function changes")
    print("   📋 Explicit versioning: Good for semantic versioning (v1.2.3)")
    print("   🚫 No versioning: When version tracking isn't needed")
    
    print("\n9. RDF Output Sample")
    print("   Versions are stored as metadata in the knowledge graph:")
    
    # Show a sample of the RDF output
    with open(file_path, "r") as f:
        content = f.read()
        lines = content.split('\n')
        version_lines = [line for line in lines if 'version' in line.lower()]
        for line in version_lines[:5]:  # Show first 5 version-related lines
            print(f"   {line}")
        if len(version_lines) > 5:
            print(f"   ... ({len(version_lines) - 5} more version lines)")

if USE_PERSISTENT_FILES:
    # Use regular directory for development/debugging
    output_dir = "examples_output"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "versioning_demo.ttl")
    print(f"Using persistent files in: {os.path.abspath(output_dir)}")
    kg = KG(backend="rdf_file", file_path=file_path, format="turtle")
    
    # Override the global system recorder to use our test KG
    from kgcore.decorators.event import _rec
    original_kg = _rec.kg
    _rec.kg = kg
    
    try:
        run_demo()
    finally:
        # Restore original KG
        _rec.kg = original_kg
else:
    # Use temp directory for clean examples
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "versioning_demo.ttl")
        kg = KG(backend="rdf_file", file_path=file_path, format="turtle")
        
        # Override the global system recorder to use our test KG
        from kgcore.decorators.event import _rec
        original_kg = _rec.kg
        _rec.kg = kg
        
        try:
            run_demo()
        finally:
            # Restore original KG
            _rec.kg = original_kg

print("\n🎉 Versioning demo completed!")
print("\nKey Benefits:")
print("✅ Automatic version tracking for code provenance")
print("✅ Change detection through function hashing")
print("✅ Flexible versioning strategies")
print("✅ Integration with knowledge graph metadata")
print("✅ RDF serialization for interoperability")