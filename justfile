# Install development dependencies
install:
    uv sync

# Format and lint all code (Python + Rust)
format:
    uvx ruff check src/ --fix
    uvx ruff format src/
    uv run mypy src/

# Run tests
test:
    uv run pytest

# Clean build artifacts
clean:
    find src/ -name "*.pyc" -delete
    find src/ -name "__pycache__" -delete

# Run a local documentation development server
docs:
    uv run mkdocs serve

# Build documentation and package
build:
    uv run mkdocs build
    uv build
