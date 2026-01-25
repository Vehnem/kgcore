"""CLI interface for kgcore."""
import sys
import os
import subprocess
import json
from pathlib import Path
from typing import Optional

try:
    import click
except ImportError:
    print(
        "Error: click is not installed. Install dev dependencies with: pip install -e '.[dev]'",
        file=sys.stderr,
    )
    sys.exit(1)


def _run_command(cmd: list[str]) -> int:
    """Run a command and return exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent.parent)
    return result.returncode




@click.group()
@click.version_option()
def cli():
    """KGcore command-line interface."""
    pass


@cli.command()
@click.option(
    "--html",
    is_flag=True,
    help="Generate HTML coverage report",
)
@click.option(
    "--min",
    "min_coverage",
    type=float,
    default=None,
    help="Fail if coverage is below this percentage",
)
def test_cov(html: bool, min_coverage: float | None):
    """Run tests with coverage report."""
    # Base pytest command with coverage
    cmd = [
        "pytest",
        "src/kgcore/tests",
        "--cov=src/kgcore",
        "--cov-report=term",
    ]
    
    # Add HTML report if requested
    if html:
        cmd.append("--cov-report=html")
    
    # Add minimum coverage if specified
    if min_coverage is not None:
        cmd.append(f"--cov-fail-under={min_coverage}")
    
    # Run the command
    exit_code = _run_command(cmd)
    
    if html and exit_code == 0:
        print("\nHTML coverage report generated in: htmlcov/index.html")
    
    sys.exit(exit_code)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path (default: stdout or input_file with new extension)",
)
@click.option(
    "--input-format", "-if",
    type=str,
    help="Input RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified.",
)
@click.option(
    "--output-format", "-of",
    type=str,
    default="turtle",
    help="Output RDF format (default: turtle)",
)
@click.option(
    "--to-core",
    is_flag=True,
    help="Convert to CoreGraph JSON format instead of RDF",
)
@click.option(
    "--mode",
    type=str,
    default="simple",
    help="Conversion mode (simple, reified_edges, quads_with_context)",
)
def convert(input_file: str, output: Optional[str], input_format: Optional[str], 
            output_format: str, to_core: bool, mode: str):
    """
    Convert RDF files between formats or to CoreGraph.
    
    Examples:
    
    \b
        # Convert Turtle to N3
        kgcore convert data.ttl -of n3 -o data.n3
        
    \b
        # Convert to CoreGraph JSON
        kgcore convert data.ttl --to-core -o data.json
        
    \b
        # Convert with specific mode
        kgcore convert data.ttl --to-core --mode reified_edges
    """
    from kgcore.api.cgm import RDFBackend
    from kgcore.api.rdf_store import FileRDFStore
    from rdflib import Graph
    from rdflib.util import guess_format
    
    input_path = Path(input_file)
    
    # Determine input format
    if input_format is None:
        input_format = guess_format(str(input_path)) or "turtle"
    
    try:
        if to_core:
            # Convert RDF to CoreGraph
            rdf_graph = Graph()
            rdf_graph.parse(str(input_path), format=input_format)
            
            backend = RDFBackend()
            result = backend.to_core(rdf_graph, mode=mode)
            core = result.graph
            
            # Convert CoreGraph to JSON
            core_dict = {
                "nodes": [
                    {
                        "id": str(node.id),
                        "labels": node.labels,
                        "properties": {
                            k: {
                                "value": v.value,
                                "datatype": v.datatype,
                                "language": v.language
                            } if hasattr(v, "value") else str(v)
                            for k, v in node.properties.items()
                        }
                    }
                    for node in core.nodes.values()
                ],
                "edges": [
                    {
                        "id": str(edge.id),
                        "source": str(edge.source),
                        "target": str(edge.target),
                        "label": edge.label,
                        "properties": {
                            k: {
                                "value": v.value,
                                "datatype": v.datatype,
                                "language": v.language
                            } if hasattr(v, "value") else str(v)
                            for k, v in edge.properties.items()
                        }
                    }
                    for edge in core.edges.values()
                ],
                "metadata": core.metadata,
                "warnings": result.warnings
            }
            
            output_text = json.dumps(core_dict, indent=2)
            
            if output:
                output_path = Path(output)
                output_path.write_text(output_text)
                click.echo(f"CoreGraph saved to {output_path}")
            else:
                click.echo(output_text)
                
            if result.warnings:
                click.echo("\nWarnings:", err=True)
                for warning in result.warnings:
                    click.echo(f"  - {warning}", err=True)
        else:
            # Convert RDF to RDF (format conversion)
            rdf_graph = Graph()
            rdf_graph.parse(str(input_path), format=input_format)
            
            # Determine output path
            if output:
                output_path = Path(output)
            else:
                # Generate output path with new extension
                ext_map = {
                    "turtle": ".ttl",
                    "n3": ".n3",
                    "xml": ".rdf",
                    "json-ld": ".jsonld",
                }
                ext = ext_map.get(output_format, ".ttl")
                output_path = input_path.with_suffix(ext)
            
            # Serialize to output format
            rdf_graph.serialize(destination=str(output_path), format=output_format)
            click.echo(f"Converted {input_path} to {output_path} ({output_format})")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--format", "-f",
    type=str,
    help="RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified.",
)
@click.option(
    "--query", "-q",
    type=str,
    help="SPARQL query string (if not provided, reads from stdin)",
)
@click.option(
    "--query-file", "-qf",
    type=click.Path(exists=True),
    help="File containing SPARQL query",
)
@click.option(
    "--output-format",
    type=click.Choice(["table", "json", "csv"], case_sensitive=False),
    default="table",
    help="Output format for query results (default: table)",
)
def query(input_file: str, format: Optional[str], query: Optional[str], 
          query_file: Optional[str], output_format: str):
    """
    Execute SPARQL queries on RDF files.
    
    Examples:
    
    \b
        # Query from command line
        kgcore query data.ttl -q "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
        
    \b
        # Query from file
        kgcore query data.ttl -qf query.sparql
        
    \b
        # Output as JSON
        kgcore query data.ttl -q "SELECT * WHERE { ?s ?p ?o }" --output-format json
    """
    from kgcore.api.cgm import RDFBackend
    from kgcore.api.rdf_store import FileRDFStore
    from rdflib import Graph
    from rdflib.util import guess_format
    
    input_path = Path(input_file)
    
    # Determine input format
    if format is None:
        format = guess_format(str(input_path)) or "turtle"
    
    # Get query string
    if query_file:
        query_str = Path(query_file).read_text()
    elif query:
        query_str = query
    else:
        # Read from stdin
        click.echo("Enter SPARQL query (end with Ctrl+D or empty line):", err=True)
        lines = []
        try:
            while True:
                line = input()
                if not line.strip():
                    break
                lines.append(line)
            query_str = "\n".join(lines)
        except EOFError:
            query_str = "\n".join(lines)
        
        if not query_str.strip():
            click.echo("Error: No query provided", err=True)
            sys.exit(1)
    
    try:
        # Load RDF file
        store = FileRDFStore(str(input_path), format=format)
        backend = RDFBackend(store=store)
        
        # Execute query
        result = backend.query(query_str)
        
        # Check for errors
        if "error" in result.metadata:
            click.echo(f"Query error: {result.metadata['error']}", err=True)
            sys.exit(1)
        
        # Output results
        if output_format.lower() == "json":
            output_data = {
                "columns": result.columns,
                "rows": result.rows,
                "count": len(result)
            }
            click.echo(json.dumps(output_data, indent=2))
        elif output_format.lower() == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=result.columns)
            writer.writeheader()
            writer.writerows(result.rows)
            click.echo(output.getvalue())
        else:  # table format
            if result.columns:
                # Print header
                header = " | ".join(result.columns)
                click.echo(header)
                click.echo("-" * len(header))
                
                # Print rows
                for row in result.rows:
                    values = [str(row.get(col, "")) for col in result.columns]
                    click.echo(" | ".join(values))
            else:
                click.echo("No results")
            
            click.echo(f"\n{len(result)} result(s)", err=True)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--format", "-f",
    type=str,
    help="RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified.",
)
def info(input_file: str, format: Optional[str]):
    """
    Show information and statistics about an RDF file.
    
    Examples:
    
    \b
        # Show info about a Turtle file
        kgcore info data.ttl
        
    \b
        # Specify format explicitly
        kgcore info data.rdf -f xml
    """
    from rdflib import Graph
    from rdflib.util import guess_format
    from collections import Counter
    
    input_path = Path(input_file)
    
    # Determine input format
    if format is None:
        format = guess_format(str(input_path)) or "turtle"
    
    try:
        rdf_graph = Graph()
        rdf_graph.parse(str(input_path), format=format)
        
        # Count triples
        triple_count = len(rdf_graph)
        
        # Count subjects, predicates, objects
        subjects = set()
        predicates = set()
        objects = set()
        literal_count = 0
        
        for s, p, o in rdf_graph:
            subjects.add(s)
            predicates.add(p)
            if hasattr(o, "value"):  # Literal
                literal_count += 1
            else:
                objects.add(o)
        
        # Count namespaces
        namespaces = list(rdf_graph.namespaces())
        
        # Most common predicates
        pred_counter = Counter(str(p) for _, p, _ in rdf_graph)
        top_predicates = pred_counter.most_common(10)
        
        # Output information
        click.echo(f"File: {input_path}")
        click.echo(f"Format: {format}")
        click.echo(f"Triples: {triple_count:,}")
        click.echo(f"Unique subjects: {len(subjects):,}")
        click.echo(f"Unique predicates: {len(predicates):,}")
        click.echo(f"Unique objects: {len(objects):,}")
        click.echo(f"Literals: {literal_count:,}")
        click.echo(f"Namespaces: {len(namespaces)}")
        
        if namespaces:
            click.echo("\nNamespaces:")
            for prefix, uri in namespaces[:10]:
                click.echo(f"  {prefix}: {uri}")
            if len(namespaces) > 10:
                click.echo(f"  ... and {len(namespaces) - 10} more")
        
        if top_predicates:
            click.echo("\nTop predicates:")
            for pred, count in top_predicates:
                click.echo(f"  {pred}: {count:,}")
                
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.option(
    "--format", "-f",
    type=str,
    help="RDF format (turtle, n3, xml, json-ld, etc.). Auto-detected if not specified.",
)
@click.option(
    "--strict",
    is_flag=True,
    help="Enable strict validation (check for common issues)",
)
def validate(input_file: str, format: Optional[str], strict: bool):
    """
    Validate an RDF file for syntax errors and common issues.
    
    Examples:
    
    \b
        # Basic validation
        kgcore validate data.ttl
        
    \b
        # Strict validation with additional checks
        kgcore validate data.ttl --strict
    """
    from rdflib import Graph
    from rdflib.util import guess_format
    from rdflib.exceptions import ParserError
    
    input_path = Path(input_file)
    
    # Determine input format
    if format is None:
        format = guess_format(str(input_path)) or "turtle"
    
    errors = []
    warnings = []
    
    try:
        # Try to parse the file
        rdf_graph = Graph()
        rdf_graph.parse(str(input_path), format=format)
        
        click.echo(f"✓ File parsed successfully ({format} format)")
        click.echo(f"✓ Found {len(rdf_graph):,} triples")
        
        if strict:
            # Additional strict checks
            click.echo("\nRunning strict validation checks...")
            
            # Check for empty graph
            if len(rdf_graph) == 0:
                warnings.append("Graph is empty (no triples)")
            
            # Check for common issues
            subjects = set()
            predicates = set()
            objects = set()
            blank_nodes = set()
            
            for s, p, o in rdf_graph:
                subjects.add(s)
                predicates.add(p)
                if hasattr(o, "value"):
                    pass  # Literal
                else:
                    objects.add(o)
                    if hasattr(o, "n3") and o.n3().startswith("_:"):
                        blank_nodes.add(o)
                if hasattr(s, "n3") and s.n3().startswith("_:"):
                    blank_nodes.add(s)
            
            # Check for orphaned blank nodes
            if blank_nodes:
                referenced_bnodes = set()
                for s, p, o in rdf_graph:
                    if hasattr(s, "n3") and s.n3().startswith("_:"):
                        referenced_bnodes.add(s)
                    if hasattr(o, "n3") and o.n3().startswith("_:"):
                        referenced_bnodes.add(o)
                
                orphaned = blank_nodes - referenced_bnodes
                if orphaned:
                    warnings.append(f"Found {len(orphaned)} potentially orphaned blank nodes")
            
            # Check for very few predicates (might indicate parsing issues)
            if len(predicates) < 2 and len(rdf_graph) > 10:
                warnings.append(f"Very few unique predicates ({len(predicates)}) for {len(rdf_graph)} triples")
            
            # Check for common namespace issues
            if len(predicates) > 0:
                pred_strs = [str(p) for p in predicates]
                if all(not p.startswith("http://") and not p.startswith("https://") for p in pred_strs[:5]):
                    warnings.append("Some predicates may not be proper URIs")
        
        # Output results
        if warnings:
            click.echo("\nWarnings:", err=True)
            for warning in warnings:
                click.echo(f"  ⚠ {warning}", err=True)
        
        if errors:
            click.echo("\nErrors:", err=True)
            for error in errors:
                click.echo(f"  ✗ {error}", err=True)
            sys.exit(1)
        else:
            click.echo("\n✓ Validation passed")
            if warnings:
                click.echo(f"  ({len(warnings)} warning(s))", err=True)
            
    except ParserError as e:
        click.echo(f"✗ Parse error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        if strict:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"], case_sensitive=False),
    default="bash",
    help="Shell type for completion script (default: bash)",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Output file path (default: stdout)",
)
def completion(shell: str, output: Optional[str]):
    """
    Generate shell completion script for kgcore.
    
    To enable bash completion, add this to your ~/.bashrc or ~/.bash_profile:
    
    \b
        eval "$(kgcore completion --shell bash)"
    
    Or save to a file and source it:
    
    \b
        kgcore completion --shell bash -o ~/.kgcore-complete.bash
        echo "source ~/.kgcore-complete.bash" >> ~/.bashrc
    
    For zsh, add to ~/.zshrc:
    
    \b
        eval "$(kgcore completion --shell zsh)"
    
    For fish, save to ~/.config/fish/completions/kgcore.fish:
    
    \b
        kgcore completion --shell fish -o ~/.config/fish/completions/kgcore.fish
    """
    # Generate completion script based on shell type
    script = _generate_completion_script(shell.lower())
    
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(script)
        click.echo(f"Completion script written to {output_path}")
        click.echo(f"\nTo enable, add this to your ~/.{shell}rc:")
        click.echo(f"  source {output_path}")
    else:
        click.echo(script)


def _generate_completion_script(shell: str) -> str:
    """Generate shell completion script."""
    if shell == "bash":
        return _generate_bash_completion()
    elif shell == "zsh":
        return _generate_zsh_completion()
    elif shell == "fish":
        return _generate_fish_completion()
    else:
        raise ValueError(f"Unsupported shell: {shell}")


def _generate_bash_completion() -> str:
    """Generate bash completion script using Click's completion system."""
    script = """# kgcore bash completion
# This script is generated by kgcore completion command
# Source it in your ~/.bashrc or ~/.bash_profile:
#   source <(kgcore completion --shell bash)

_kgcore_completion() {
    local IFS=$'\\n'
    COMPREPLY=($(env COMP_WORDS="${COMP_WORDS[*]}" \\
        COMP_CWORD=$COMP_CWORD \\
        _KGCORE_COMPLETE=bash_complete \\
        kgcore))
}

complete -F _kgcore_completion kgcore
"""
    return script


def _generate_zsh_completion() -> str:
    """Generate zsh completion script using Click's completion system."""
    script = """# kgcore zsh completion
# This script is generated by kgcore completion command
# Source it in your ~/.zshrc:
#   source <(kgcore completion --shell zsh)

_kgcore_completion() {
    local -a completions
    completions=(${(f)"$(env COMP_WORDS="${words[*]}" \\
        COMP_CWORD=$((CURRENT-1)) \\
        _KGCORE_COMPLETE=zsh_complete \\
        kgcore)"})
    _describe 'kgcore' completions
}

compdef _kgcore_completion kgcore
"""
    return script


def _generate_fish_completion() -> str:
    """Generate fish completion script using Click's completion system."""
    script = """# kgcore fish completion
# This script is generated by kgcore completion command
# Place it in ~/.config/fish/completions/kgcore.fish

function __kgcore_complete
    env _KGCORE_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) kgcore
end

complete -c kgcore -a "(__kgcore_complete)"
"""
    return script


# Backend configuration context
class BackendContext:
    """Context for managing backend configuration across CLI commands."""
    
    def __init__(self, backend_type: str = "rdf_file", **kwargs):
        self.backend_type = backend_type
        self.kwargs = kwargs
        self._backend = None
        self._store = None
    
    def get_backend(self):
        """Get or create the backend instance."""
        if self._backend is None:
            if self.backend_type == "rdf_file":
                from kgcore.api.rdf_store import FileRDFStore
                file_path = self.kwargs.get("file_path", "kgcore_data.ttl")
                format = self.kwargs.get("format", "turtle")
                auto_save = self.kwargs.get("auto_save", True)
                self._store = FileRDFStore(file_path, format=format, auto_save=auto_save)
                from kgcore.api.cgm import RDFBackend
                self._backend = RDFBackend(store=self._store)
            elif self.backend_type == "memory":
                from kgcore.api.rdf_store import InMemoryRDFStore
                from kgcore.api.cgm import RDFBackend
                self._store = InMemoryRDFStore()
                self._backend = RDFBackend(store=self._store)
            else:
                raise ValueError(f"Unknown backend type: {self.backend_type}")
        return self._backend
    
    def get_store(self):
        """Get the underlying store."""
        if self._store is None:
            self.get_backend()  # Initialize if needed
        return self._store


def _parse_input_format(input_data: str, input_format: str):
    """Parse input data in various formats and return a CoreGraph."""
    from kgcore.api.cgm import CoreGraph, CoreNode, CoreEdge, CoreLiteral
    
    if input_format == "core" or input_format == "json":
        # Parse CoreGraph JSON
        try:
            data = json.loads(input_data)
            core = CoreGraph()
            
            # Add nodes
            for node_data in data.get("nodes", []):
                node = CoreNode(
                    id=node_data["id"],
                    labels=node_data.get("labels", []),
                    properties={
                        k: CoreLiteral(**v) if isinstance(v, dict) and "value" in v else v
                        for k, v in node_data.get("properties", {}).items()
                    }
                )
                core.add_node(node)
            
            # Add edges
            for edge_data in data.get("edges", []):
                edge = CoreEdge(
                    id=edge_data["id"],
                    source=edge_data["source"],
                    target=edge_data["target"],
                    label=edge_data["label"],
                    properties={
                        k: CoreLiteral(**v) if isinstance(v, dict) and "value" in v else v
                        for k, v in edge_data.get("properties", {}).items()
                    }
                )
                core.add_edge(edge)
            
            return core
        except json.JSONDecodeError as e:
            raise click.BadParameter(f"Invalid JSON: {e}")
    
    elif input_format == "rdf":
        # Parse RDF (Turtle, N3, etc.)
        from rdflib import Graph
        from rdflib.util import guess_format
        
        rdf_format = guess_format("input") or "turtle"
        graph = Graph()
        try:
            graph.parse(data=input_data, format=rdf_format)
            backend = _get_default_backend()
            result = backend.to_core(graph, mode="simple")
            return result.graph
        except Exception as e:
            raise click.BadParameter(f"Failed to parse RDF: {e}")
    
    elif input_format == "triple":
        # Parse inline triple format: "subject predicate object"
        # Objects can be URIs or literals (strings without http:// or quotes)
        from rdflib import URIRef, Literal, RDF
        from kgcore.api.cgm import CoreGraph, CoreNode, CoreEdge, CoreLiteral
        
        core = CoreGraph()
        parts = input_data.strip().split(None, 2)  # Split on whitespace, max 3 parts
        if len(parts) != 3:
            raise click.BadParameter("Triple format requires exactly 3 parts: subject predicate object")
        
        s, p, o = parts
        
        # Determine if object is a literal (not a URI)
        is_literal = not (o.startswith("http://") or o.startswith("https://") or 
                          o.startswith("<") or ":" in o.split()[0])
        
        # Create subject node
        if s not in core.nodes:
            core.add_node(CoreNode(id=s, labels=[], properties={}))
        
        if is_literal:
            # Object is a literal - add as property on subject
            # Remove quotes if present
            literal_value = o.strip('"\'')
            if s in core.nodes:
                core.nodes[s].properties[p] = CoreLiteral(value=literal_value)
        else:
            # Object is a URI/node - create object node and edge
            if o not in core.nodes:
                core.add_node(CoreNode(id=o, labels=[], properties={}))
            
            # Create edge
            edge_id = f"{s}_{p}_{o}"
            core.add_edge(CoreEdge(
                id=edge_id,
                source=s,
                target=o,
                label=p,
                properties={}
            ))
        
        return core
    
    else:
        raise click.BadParameter(f"Unknown input format: {input_format}")


def _get_default_backend():
    """Get a default backend for conversions."""
    from kgcore.api.cgm import RDFBackend
    return RDFBackend()


@cli.group()
@click.option(
    "--backend",
    type=click.Choice(["rdf_file", "memory"], case_sensitive=False),
    default="rdf_file",
    help="Backend type (default: rdf_file)",
)
@click.option(
    "--file", "file_path",
    type=click.Path(),
    default="kgcore_data.ttl",
    help="RDF file path (for rdf_file backend)",
)
@click.option(
    "--format", "-f",
    type=str,
    default="turtle",
    help="RDF format (default: turtle)",
)
@click.option(
    "--auto-save/--no-auto-save",
    default=True,
    help="Automatically save changes (default: True)",
)
@click.pass_context
def graph(ctx, backend: str, file_path: str, format: str, auto_save: bool):
    """
    Graph mutation operations.
    
    Configure a backend and perform mutations (add, delete, merge).
    
    Examples:
    
    \b
        # Add data to a file-based RDF backend
        kgcore graph --file data.ttl add --core '{"nodes":[...]}'
        
    \b
        # Use in-memory backend
        kgcore graph --backend memory add --triple "s p o"
    """
    ctx.ensure_object(dict)
    ctx.obj["backend_ctx"] = BackendContext(
        backend_type=backend,
        file_path=file_path,
        format=format,
        auto_save=auto_save
    )


@graph.command()
@click.option(
    "--core", "--json",
    "input_core",
    type=str,
    help="CoreGraph JSON data (string or @file path)",
)
@click.option(
    "--rdf",
    type=str,
    help="RDF data (string or @file path)",
)
@click.option(
    "--triple",
    type=str,
    help="Single triple: 'subject predicate object'",
)
@click.option(
    "--file", "input_file",
    type=click.Path(exists=True),
    help="Input file (format auto-detected or use --format)",
)
@click.option(
    "--input-format", "-if",
    type=click.Choice(["core", "json", "rdf", "triple"], case_sensitive=False),
    help="Input format (for --file, auto-detected if not specified)",
)
@click.option(
    "--mode",
    type=str,
    default="simple",
    help="Conversion mode (default: simple)",
)
@click.pass_context
def add(ctx, input_core: Optional[str], rdf: Optional[str], triple: Optional[str],
        input_file: Optional[str], input_format: Optional[str], mode: str):
    """
    Add data to the configured backend.
    
    Supports multiple input formats that are automatically converted to the backend's format.
    
    Examples:
    
    \b
        # Add from CoreGraph JSON
        kgcore graph --file data.ttl add --core '{"nodes":[{"id":"a","labels":["Person"]}]}'
        
    \b
        # Add from RDF file
        kgcore graph --file data.ttl add --file input.ttl --input-format rdf
        
    \b
        # Add a single triple
        kgcore graph --file data.ttl add --triple "http://ex/alice http://ex/name Alice"
    """
    backend_ctx = ctx.obj["backend_ctx"]
    backend = backend_ctx.get_backend()
    
    # Determine input source
    input_data = None
    detected_format = None
    
    if input_core:
        input_data = input_core
        detected_format = "core"
    elif rdf:
        input_data = rdf
        detected_format = "rdf"
    elif triple:
        input_data = triple
        detected_format = "triple"
    elif input_file:
        file_path = Path(input_file)
        input_data = file_path.read_text()
        
        # Auto-detect format if not specified
        if not input_format:
            if file_path.suffix in [".json", ".jsonld"]:
                detected_format = "core"
            else:
                detected_format = "rdf"
        else:
            detected_format = input_format.lower()
    else:
        click.echo("Error: Must provide one of --core, --rdf, --triple, or --file", err=True)
        sys.exit(1)
    
    # Handle @file syntax for reading from file
    if input_data.startswith("@"):
        file_path = Path(input_data[1:])
        if not file_path.exists():
            click.echo(f"Error: File not found: {file_path}", err=True)
            sys.exit(1)
        input_data = file_path.read_text()
    
    try:
        # Parse input to CoreGraph
        core = _parse_input_format(input_data, detected_format)
        
        # Convert CoreGraph to backend format and add
        result = backend.from_core(core, mode=mode, target_store=True)
        
        click.echo(f"✓ Added {len(core.nodes)} node(s) and {len(core.edges)} edge(s)")
        
        if result.warnings:
            for warning in result.warnings:
                click.echo(f"  ⚠ {warning}", err=True)
        
        # Save if not auto-saving
        if not backend_ctx.kwargs.get("auto_save", True):
            store = backend_ctx.get_store()
            if hasattr(store, "save"):
                store.save()
                click.echo("✓ Changes saved")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@graph.command()
@click.option(
    "--pattern",
    type=str,
    required=True,
    help="Triple pattern to match (subject predicate object, use * for wildcard)",
)
@click.pass_context
def delete(ctx, pattern: str):
    """
    Delete data matching a pattern from the configured backend.
    
    Examples:
    
    \b
        # Delete all triples with a specific subject
        kgcore graph --file data.ttl delete --pattern "http://ex/alice * *"
        
    \b
        # Delete all triples with a specific predicate
        kgcore graph --file data.ttl delete --pattern "* http://ex/name *"
    """
    backend_ctx = ctx.obj["backend_ctx"]
    store = backend_ctx.get_store()
    
    # Parse pattern
    parts = pattern.strip().split()
    if len(parts) != 3:
        click.echo("Error: Pattern must have 3 parts: subject predicate object", err=True)
        sys.exit(1)
    
    from rdflib import URIRef, Literal
    
    def parse_term(term: str):
        """Parse a term (URIRef, Literal, or None for wildcard)."""
        if term == "*" or term == "None":
            return None
        if term.startswith('"') and term.endswith('"'):
            # Literal
            return Literal(term[1:-1])
        return URIRef(term)
    
    s, p, o = [parse_term(part) for part in parts]
    
    try:
        # Find matching triples
        matches = list(store.triples((s, p, o)))
        
        if not matches:
            click.echo("No matching triples found")
            return
        
        # Remove matching triples
        for match_s, match_p, match_o in matches:
            store.remove_triple(match_s, match_p, match_o)
        
        click.echo(f"✓ Deleted {len(matches)} triple(s)")
        
        # Save if not auto-saving
        if not backend_ctx.kwargs.get("auto_save", True):
            if hasattr(store, "save"):
                store.save()
                click.echo("✓ Changes saved")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@graph.command()
@click.argument("source_file", type=click.Path(exists=True))
@click.option(
    "--format", "-f",
    type=str,
    help="Source file format (auto-detected if not specified)",
)
@click.option(
    "--mode",
    type=str,
    default="simple",
    help="Conversion mode (default: simple)",
)
@click.pass_context
def merge(ctx, source_file: str, format: Optional[str], mode: str):
    """
    Merge data from a source file into the configured backend.
    
    The source file is converted to the backend's format before merging.
    
    Examples:
    
    \b
        # Merge RDF file into backend
        kgcore graph --file data.ttl merge source.ttl
        
    \b
        # Merge CoreGraph JSON
        kgcore graph --file data.ttl merge source.json --format core
    """
    backend_ctx = ctx.obj["backend_ctx"]
    backend = backend_ctx.get_backend()
    
    source_path = Path(source_file)
    
    # Auto-detect format
    if not format:
        if source_path.suffix in [".json"]:
            format = "core"
        else:
            format = "rdf"
    
    try:
        # Load source data
        source_data = source_path.read_text()
        
        # Parse to CoreGraph
        core = _parse_input_format(source_data, format)
        
        # Convert and merge into backend
        result = backend.from_core(core, mode=mode, target_store=True)
        
        click.echo(f"✓ Merged {len(core.nodes)} node(s) and {len(core.edges)} edge(s)")
        
        if result.warnings:
            for warning in result.warnings:
                click.echo(f"  ⚠ {warning}", err=True)
        
        # Save if not auto-saving
        if not backend_ctx.kwargs.get("auto_save", True):
            store = backend_ctx.get_store()
            if hasattr(store, "save"):
                store.save()
                click.echo("✓ Changes saved")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Handle Click completion requests
if "_KGCORE_COMPLETE" in os.environ:
    from click.shell_completion import get_completion_class
    shell = os.environ.get("_KGCORE_COMPLETE", "").rsplit("_", 1)[-1]
    if shell in ("bash", "zsh", "fish"):
        completion_class = get_completion_class(shell)
        if completion_class:
            comp = completion_class(cli, {}, "", "")
            print(comp.source())
            sys.exit(0)


if __name__ == "__main__":
    cli()

