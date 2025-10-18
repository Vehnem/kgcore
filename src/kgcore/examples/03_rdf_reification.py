# examples/03_rdf_reification.py
from kgcore.api import KG
import os

# Configuration: Set to True for development/debugging (keeps files)
# Set to False for clean examples (uses temp directory)
USE_PERSISTENT_FILES = True

if USE_PERSISTENT_FILES:
    # Use regular directory for development/debugging
    output_dir = "examples_output"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "reification_example.ttl")
    print(f"Using persistent files in: {os.path.abspath(output_dir)}")
else:
    # Use temp directory for clean examples
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "reification_example.ttl")

# Create a knowledge graph with RDF backend
kg = KG(backend="rdf_file", file_path=file_path, format="turtle")

# Create entities and relations
ada = kg.create_entity(["Person"], {"name": "Ada", "born": 1815})
charles = kg.create_entity(["Person"], {"name": "Charles", "born": 1791})
machine = kg.create_entity(["Machine"], {"name": "Analytical Engine"})

# Create a relation
knows_rel = kg.create_relation("KNOWS", ada.id, charles.id, {"since": 1843})

print("Created entities and relations:")
print("Entities:", [e.props for e in kg.find_entities("Person")])
print("Relations:", [r.type for r in kg.find_relations("KNOWS")])

# Add metadata using reification
print("\n--- Adding metadata using reification ---")
kg.add_meta(ada.id, {"confidence": 0.95, "source": "historical_records"})
kg.add_meta(knows_rel.id, {"confidence": 0.9, "verified_by": "biographer"})
kg.add_meta(charles.id, {"reliability": "high", "last_updated": "2024"})

print("Metadata added to entities and relations")

# Show the RDF content with reification
print("\n--- RDF Content with Reification ---")
with open(file_path, "r") as f:
    print(f.read())

# Clean up if using temp directory
if not USE_PERSISTENT_FILES:
    os.remove(file_path)
    print(f"\nCleaned up temporary file: {file_path}")
