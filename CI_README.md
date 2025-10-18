# GitLab CI Configuration

This repository includes a GitLab CI workflow that automatically builds the project and runs tests.

## CI Pipeline Overview

The CI pipeline consists of two main stages:

### 1. Build Stage
- **Image**: `ghcr.io/astral-sh/uv:debian`
- **Purpose**: Install dependencies and build the package using `uv`
- **Steps**:
  - Use pre-built `uv` image with Python 3.12
  - Create virtual environment with `uv venv`
  - Install project dependencies with `uv pip install .`
  - Install development dependencies (pytest, rdflib, pydantic)
- **Artifacts**: Virtual environment (expires in 1 hour)

### 2. Test Stage
- **Image**: `ghcr.io/astral-sh/uv:debian`
- **Purpose**: Run tests and examples using `uv`
- **Dependencies**: Build stage artifacts
- **Steps**:
  - Use `uv run` to execute commands in virtual environment
  - Set PYTHONPATH for proper module resolution
  - Run pytest on all test files with `uv run pytest`
  - Run example scripts with `uv run python`
- **Artifacts**: Test results (JUnit XML format)

## Test Coverage

The CI runs the following test suites:

- `test_meta.py` - Decorator functionality and system graph
- `test_ontology.py` - Ontology API tests
- `test_rdf_file.py` - RDF file persistence backend
- `test_rdf_reification.py` - RDF reification implementation
- `test_reification.py` - Reification functionality
- `test_smoke.py` - Basic smoke tests
- `test_versioning.py` - Versioning system tests

**Total**: 19 tests covering all major functionality

## Example Verification

The CI also runs key examples to ensure they work:

- `01_minimal_inmemory.py` - Basic KG operations
- `02_rdf_file_persistence.py` - RDF file persistence
- `03_rdf_reification.py` - RDF reification demo

## Local Testing

To test the CI configuration locally:

```bash
# 1. Ensure virtual environment exists
uv venv

# 2. Install dependencies
uv pip install .
uv pip install pytest rdflib pydantic

# 3. Run tests
export PYTHONPATH=/path/to/kgcore/src
uv run pytest src/kgcore/tests/ -v --tb=short

# 4. Run examples
uv run python -m kgcore.examples.01_minimal_inmemory
```

## CI Configuration Details

### Variables
- `PYTHON_VERSION`: "3.12" (Python version to use)

### Artifacts
- **Build artifacts**: Virtual environment (1 hour expiry)
- **Test artifacts**: JUnit XML test results (1 week expiry)

### Dependencies
- **Core**: rdflib, pydantic
- **Development**: pytest
- **Package manager**: uv (pre-installed in image)

## Pipeline Triggers

The CI pipeline runs on:
- Push to any branch
- Merge requests
- Manual triggers

## Expected Results

A successful CI run should show:
- ✅ Build stage completes without errors
- ✅ All 19 tests pass
- ✅ Examples run successfully
- ✅ No critical failures

## Troubleshooting

### Common Issues

1. **Module not found errors**: Ensure PYTHONPATH is set correctly
2. **Missing dependencies**: Check that all required packages are installed
3. **Test failures**: Review test output for specific error messages
4. **Example failures**: Check that examples can run independently

### Debug Commands

```bash
# Check Python and uv versions
python --version
uv --version

# List installed packages
uv pip list

# Run specific test
uv run pytest src/kgcore/tests/test_meta.py -v

# Run with more verbose output
uv run pytest src/kgcore/tests/ -v -s --tb=long
```

## Performance

- **Build time**: ~2-3 minutes
- **Test time**: ~1-2 minutes
- **Total pipeline time**: ~3-5 minutes

The CI is optimized for speed while maintaining comprehensive test coverage.
