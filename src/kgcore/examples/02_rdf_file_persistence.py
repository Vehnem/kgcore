# examples/02_rdf_file_persistence.py
from kgcore.api import KG
import os

# Configuration: Set to True for development/debugging (keeps files)
# Set to False for clean examples (uses temp directory)
USE_PERSISTENT_FILES = True

if USE_PERSISTENT_FILES:
    # Use regular directory for development/debugging
    output_dir = "examples_output"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "example_kg.ttl")
    print(f"Using persistent files in: {os.path.abspath(output_dir)}")
else:
    # Use temp directory for clean examples
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "example_kg.ttl")

# Create a knowledge graph with file persistence
kg = KG(backend="rdf_file", file_path=file_path, format="turtle")

# Create some entities and relations
ada = kg.create_entity(["Person"], {"name": "Ada", "born": 1815})
charles = kg.create_entity(["Person"], {"name": "Charles", "born": 1791})
machine = kg.create_entity(["Machine"], {"name": "Analytical Engine"})

# Create relations
knows_rel = kg.create_relation("KNOWS", ada.id, charles.id, {"since": 1843})
invented_rel = kg.create_relation("INVENTED", charles.id, machine.id, {"year": 1837})

# Add metadata
kg.add_meta(knows_rel.id, {"confidence": 0.9})
kg.add_meta(invented_rel.id, {"confidence": 1.0})

print("Created entities and relations with file persistence")
print("Entities:", [e.props for e in kg.find_entities("Person")])
print("Relations:", [r.type for r in kg.find_relations("KNOWS")])

# The data is automatically saved to the file
print(f"\nData saved to: {os.path.abspath(file_path)}")

# Demonstrate loading from existing file
print("\n--- Loading from existing file ---")
kg2 = KG(backend="rdf_file", file_path=file_path, format="turtle")
print("Loaded entities:", [e.props for e in kg2.find_entities("Person")])
print("Loaded relations:", [r.type for r in kg2.find_relations()])

# Show the RDF content
print("\n--- RDF Content ---")
with open(file_path, "r") as f:
    print(f.read())

# Clean up if using temp directory
if not USE_PERSISTENT_FILES:
    os.remove(file_path)
    print(f"\nCleaned up temporary file: {file_path}")
