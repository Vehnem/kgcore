# kgcore CLI Reference

The kgcore command-line interface provides tools for working with knowledge graphs from the terminal, supporting format conversion, querying, validation, and graph mutations.

## Installation

After installing kgcore, the `kgcore` command is available:

```bash
pip install -e .
kgcore --help
```

## Commands Overview

- [`convert`](#convert) - Convert RDF files between formats or to CoreGraph
- [`query`](#query) - Execute SPARQL queries on RDF files
- [`info`](#info) - Show graph statistics and information
- [`validate`](#validate) - Validate RDF files for syntax errors
- [`graph`](#graph) - Graph mutation operations (add, delete, merge)
- [`completion`](#completion) - Generate shell completion scripts
- [`test-cov`](#test-cov) - Run tests with coverage report

## Convert

Convert RDF files between formats or to CoreGraph JSON.

### Basic Usage

```bash
# Convert Turtle to N3
kgcore convert data.ttl -of n3 -o data.n3

# Convert to CoreGraph JSON
kgcore convert data.ttl --to-core -o data.json

# Convert with specific mode
kgcore convert data.ttl --to-core --mode reified_edges
```

### Options

- `--output, -o`: Output file path (default: stdout or input_file with new extension)
- `--input-format, -if`: Input RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified
- `--output-format, -of`: Output RDF format (default: turtle)
- `--to-core`: Convert to CoreGraph JSON format instead of RDF
- `--mode`: Conversion mode (simple, reified_edges, quads_with_context)

## Query

Execute SPARQL queries on RDF files.

### Basic Usage

```bash
# Query from command line
kgcore query data.ttl -q "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"

# Query from file
kgcore query data.ttl -qf query.sparql

# Output as JSON
kgcore query data.ttl -q "SELECT * WHERE { ?s ?p ?o }" --output-format json
```

### Options

- `--format, -f`: RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified
- `--query, -q`: SPARQL query string (if not provided, reads from stdin)
- `--query-file, -qf`: File containing SPARQL query
- `--output-format`: Output format for query results (table, json, csv) (default: table)

## Info

Show information and statistics about an RDF file.

### Basic Usage

```bash
# Show info about a Turtle file
kgcore info data.ttl

# Specify format explicitly
kgcore info data.rdf -f xml
```

### Options

- `--format, -f`: RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified

### Output

The `info` command displays:
- File path and format
- Triple count
- Unique subjects, predicates, and objects
- Literal count
- Namespace information
- Top predicates by frequency

## Validate

Validate RDF files for syntax errors and common issues.

### Basic Usage

```bash
# Basic validation
kgcore validate data.ttl

# Strict validation with additional checks
kgcore validate data.ttl --strict
```

### Options

- `--format, -f`: RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified
- `--strict`: Enable strict validation (check for common issues)

### Strict Mode Checks

When `--strict` is enabled, the validator performs additional checks:
- Empty graph detection
- Orphaned blank node detection
- Unusual predicate patterns
- Namespace validation

## Graph Mutations

The `graph` command group provides operations for mutating graphs with format abstraction. All input formats are automatically converted to the backend's native format.

### Backend Configuration

```bash
# Use file-based RDF backend (default)
kgcore graph --file data.ttl [command]

# Use in-memory backend
kgcore graph --backend memory [command]

# Configure format and auto-save
kgcore graph --file data.ttl --format n3 --no-auto-save [command]
```

### Options

- `--backend`: Backend type (rdf_file, memory) (default: rdf_file)
- `--file`: RDF file path (for rdf_file backend) (default: kgcore_data.ttl)
- `--format, -f`: RDF format (default: turtle)
- `--auto-save/--no-auto-save`: Automatically save changes (default: True)

### Add Command

Add data to the configured backend from various input formats.

```bash
# Add from CoreGraph JSON
kgcore graph --file data.ttl add --core '{"nodes":[{"id":"a","labels":["Person"]}]}'

# Add from RDF file
kgcore graph --file data.ttl add --file input.ttl --input-format rdf

# Add a single triple (auto-detects literals vs URIs)
kgcore graph --file data.ttl add --triple "http://ex/alice http://ex/name Alice"
kgcore graph --file data.ttl add --triple "http://ex/alice http://ex/knows http://ex/bob"
```

#### Input Formats

- `--core, --json`: CoreGraph JSON data (string or @file path)
- `--rdf`: RDF data (string or @file path)
- `--triple`: Single triple: 'subject predicate object'
- `--file`: Input file (format auto-detected or use --input-format)
- `--input-format, -if`: Input format (core, json, rdf, triple)
- `--mode`: Conversion mode (default: simple)

### Delete Command

Delete data matching a pattern from the configured backend.

```bash
# Delete all triples with a specific subject
kgcore graph --file data.ttl delete --pattern "http://ex/alice * *"

# Delete all triples with a specific predicate
kgcore graph --file data.ttl delete --pattern "* http://ex/name *"
```

#### Pattern Format

Patterns use the format: `subject predicate object` where `*` matches anything.

### Merge Command

Merge data from a source file into the configured backend.

```bash
# Merge RDF file into backend
kgcore graph --file data.ttl merge source.ttl

# Merge CoreGraph JSON
kgcore graph --file data.ttl merge source.json --format core
```

#### Options

- `--format, -f`: Source file format (auto-detected if not specified)
- `--mode`: Conversion mode (default: simple)

## Example Workflow

Here's a complete workflow demonstrating graph mutations with format abstraction:

```bash
# 1. Create a new graph file with a triple
kgcore graph --file my_kg.ttl add --triple "http://ex/alice http://ex/name Alice"

# 2. Add more data from CoreGraph JSON
kgcore graph --file my_kg.ttl add --core '{"nodes":[{"id":"http://ex/bob","labels":["Person"],"properties":{"http://ex/name":"Bob"}}],"edges":[]}'

# 3. Add a relationship
kgcore graph --file my_kg.ttl add --triple "http://ex/alice http://ex/knows http://ex/bob"

# 4. Merge existing RDF file
kgcore graph --file my_kg.ttl merge existing_data.ttl

# 5. View graph information
kgcore info my_kg.ttl

# 6. Query the graph
kgcore query my_kg.ttl -q "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"

# 7. Delete specific data
kgcore graph --file my_kg.ttl delete --pattern "* http://ex/name *"

# 8. Validate the result
kgcore validate my_kg.ttl

# 9. Convert to CoreGraph JSON for inspection
kgcore convert my_kg.ttl --to-core -o my_kg.json
```

### Format Abstraction

The key feature of the graph mutation commands is **format abstraction**: you can input data in any format (CoreGraph JSON, RDF, triples), and it will be automatically converted to the backend's native format. For example:

- Input: CoreGraph JSON → Converted to RDF → Stored in RDF file backend
- Input: RDF Turtle → Converted to CoreGraph → Converted to RDF → Stored in RDF file backend
- Input: Triple string → Converted to CoreGraph → Converted to RDF → Stored in RDF file backend

This allows you to work with the format that's most convenient for your use case, while the backend stores data in its optimal format.

## Completion

Generate shell completion scripts for bash, zsh, and fish.

### Basic Usage

```bash
# Generate and use immediately (bash/zsh)
eval "$(kgcore completion --shell bash)"

# Save to a file
kgcore completion --shell bash -o ~/.kgcore-complete.bash
source ~/.kgcore-complete.bash

# For zsh
kgcore completion --shell zsh -o ~/.zshrc-completions/kgcore

# For fish
kgcore completion --shell fish -o ~/.config/fish/completions/kgcore.fish
```

### Options

- `--shell`: Shell type (bash, zsh, fish) (default: bash)
- `--output, -o`: Output file path (default: stdout)

After enabling completion, you can use tab completion for commands and options:

```bash
kgcore <TAB>  # Shows: completion, convert, graph, info, query, test-cov, validate
kgcore convert <TAB>  # Shows file completions
kgcore graph <TAB>  # Shows subcommands
```

## Test Coverage

Run tests with coverage reporting.

### Basic Usage

```bash
# Basic coverage report in terminal
kgcore test-cov

# Generate HTML coverage report
kgcore test-cov --html

# Fail if coverage is below 80%
kgcore test-cov --min 80

# Combine options
kgcore test-cov --html --min 75
```

### Options

- `--html`: Generate HTML coverage report
- `--min`: Fail if coverage is below this percentage

The HTML report (when using `--html`) will be generated in `htmlcov/index.html` in your project root.

