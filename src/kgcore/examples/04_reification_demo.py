# examples/04_reification_demo.py
from kgcore.api import KG
import os

# Configuration: Set to True for development/debugging (keeps files)
# Set to False for clean examples (uses temp directory)
USE_PERSISTENT_FILES = True

if USE_PERSISTENT_FILES:
    # Use regular directory for development/debugging
    output_dir = "examples_output"
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "reification_demo.ttl")
    print(f"Using persistent files in: {os.path.abspath(output_dir)}")
else:
    # Use temp directory for clean examples
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, "reification_demo.ttl")

# Create a knowledge graph with RDF backend
kg = KG(backend="rdf_file", file_path=file_path, format="turtle")

print("=== RDF Reification Demo ===\n")

# Create entities with regular properties
ada = kg.create_entity(["Person"], {"name": "Ada", "born": 1815, "profession": "mathematician"})
charles = kg.create_entity(["Person"], {"name": "Charles", "born": 1791, "profession": "inventor"})

# Create a relation with regular properties
knows_rel = kg.create_relation("KNOWS", ada.id, charles.id, {"since": 1843, "relationship": "colleague"})

print("1. Created entities and relations with regular properties:")
print(f"   Ada: {ada.props}")
print(f"   Charles: {charles.props}")
print(f"   KNOWS relation: {knows_rel.props}")

# Add metadata using reification (this is about the statements themselves)
print("\n2. Adding metadata about the statements using reification:")
kg.add_meta(ada.id, {
    "confidence": 0.95, 
    "source": "historical_records", 
    "last_verified": "2024-01-15"
})

kg.add_meta(knows_rel.id, {
    "confidence": 0.9, 
    "verified_by": "biographer", 
    "disputed": False
})

kg.add_meta(charles.id, {
    "reliability": "high", 
    "data_quality": "excellent"
})

print("   ✓ Metadata added to statements using RDF reification")

# Show the difference in RDF output
print("\n3. RDF Output (showing reification):")
print("   Regular properties are direct triples on entities/relations")
print("   Reified metadata creates rdf:Statement nodes with metadata")
print()

with open(file_path, "r") as f:
    content = f.read()
    print(content)

print("\n4. Key differences:")
print("   - Regular properties: direct subject-predicate-object triples")
print("   - Reified metadata: blank nodes of type rdf:Statement")
print("   - Reification allows metadata about statements themselves")
print("   - Useful for provenance, confidence, source tracking")

# Clean up if using temp directory
if not USE_PERSISTENT_FILES:
    os.remove(file_path)
    print(f"\nCleaned up temporary file: {file_path}")
