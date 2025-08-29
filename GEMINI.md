# Griffonner Project Overview

Griffonner is a template-first Python documentation generator that gets out of your way. Named after the French verb "griffonner" (to scribble/draft), it uses Griffe to parse Python code and Jinja2 templates to generate documentation in any format with zero opinions about output structure.

**Core flow**: Python Code → Griffe Parser → Template Engine → Your Output

## Design Principles

1.  **Zero opinions** - No assumptions about output format or structure
2.  **Template-first** - Templates control everything, rich context from Griffe
3.  **Composable** - Mix generated with hand-written content
4.  **Format agnostic** - Generate Markdown, RST, HTML, JSON, anything
5.  **Extensible** - Plugin system and template ecosystem

## Building and Running

The project uses `just` as a command runner. Key commands are defined in the `justfile`:

*   **Install dependencies:** `just install`
*   **Format and lint:** `just format`
*   **Run tests:** `just test` or `uv run pytest`
*   **Serve documentation locally:** `just docs`
*   **Build documentation and package:** `just build`
*   **List all available commands:** `just -l`

## Development Conventions

*   **Python Version:** Python 3.9+
*   **Linting and Formatting:** The project uses `ruff` for linting and formatting. The configuration is in `pyproject.toml`.
*   **Testing:** `pytest` is used for testing. Tests are located in the `test/` directory.
*   **Typing:** The project uses type hints and `mypy` for static type checking.
*   **Docstrings:** Google docstring style.
*   **CLI:** `Typer` is used for the CLI.
*   **Data Validation:** `Pydantic` is used over dataclasses.
*   **Writing Style:** British English, sentence case for titles.
*   **Unit Test Style:** Use `@pytest.mark.parametrize` with `pytest.param` and `id` for tests.

## Architecture

*   `src/griffonner/`: Main source code.
    *   `cli.py`: The `typer`-based command-line interface.
    *   `core.py`: Core documentation generation logic.
    *   `config.py`: Configuration loading and management.
    *   `templates.py`: Jinja2 template loading and validation.
    *   `frontmatter.py`: YAML frontmatter parsing.
    *   `griffe_wrapper.py`: Griffe integration.
    *   `watcher.py`: Watch mode implementation.
    *   `plugins/`: Plugin system.
        *   `protocols.py`: Plugin interface definitions.
        *   `base.py`: Base classes for plugins.
        *   `manager.py`: Plugin discovery & management.
*   `test/`: Pytest tests.
*   `docs/`: Project documentation in Markdown.
*   `templates/`: Default templates.
*   `pyproject.toml`: Project metadata, dependencies, and tool configuration.
*   `justfile`: Command runner recipes.

## Plugin System

Griffonner has an extensible plugin system that allows for:

*   **Processors:** Middleware that can intercept and transform Griffe objects before they are passed to the templating engine.
*   **Filters:** Custom Jinja2 filters for data transformation in templates.
*   **Bundles:** Collections of processors, filters, and templates that can be packaged together.

Plugins are discovered via setuptools entry points, and local plugins can be loaded from Python modules.

Your job is code, mine is command, review, version control
