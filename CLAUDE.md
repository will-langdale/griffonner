# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Griffonner is a template-first Python documentation generator that gets out of your way. Named after the French verb "griffonner" (to scribble/draft), it uses Griffe to parse Python code and Jinja2 templates to generate documentation in any format with zero opinions about output structure.

**Core flow**: Python Code → Griffe Parser → Template Engine → Your Output

## Development commands

This project uses `uv` for dependency management and `just` for task running:

- `uv sync` - Install development dependencies
- `just format` - Format and lint code using ruff and mypy (uses `uv run mypy`)
- `just test` - Run tests with pytest (uses `uv run pytest`)
- `uv run pytest` - Run tests directly with pytest
- `just docs` - Run local documentation development server
- `just build` - Build documentation and package
- `just clean` - Clean build artifacts
- `just -l` - List all available just commands

## Code style and standards

**Python requirements**:
- Python 3.9+ with typing (`from typing import List, Dict, Optional, Union` - no built-in generic types)
- Google docstring style
- Use Pydantic over dataclasses
- Use Typer for CLI implementation
- Ruff for linting/formatting (88 char line length)
- MyPy for type checking

**Test style**:
```python
@pytest.mark.parametrize(
    ["foo", "bar"],
    [
        pytest.param(True, 12, id="test_thing"),
        pytest.param(False, 16, id="test_other_thing"),
    ],
)
def test_something(foo: bool, bar: int):
    """Tests that something does something."""
```

**Writing style**:
- British English
- Sentence case for titles

## Planned architecture

**Target package structure**:
```
src/griffonner/
├── cli.py              # Typer-based CLI
├── core.py             # Main generation logic
├── frontmatter.py      # YAML frontmatter parsing
├── templates.py        # Template discovery & loading
├── griffe_wrapper.py   # Griffe integration
└── plugins/            # Plugin system
```

**Built-in templates structure**:
```
templates/
├── python/
│   ├── default/        # Basic Python templates
│   ├── sphinx-style/   # Sphinx-compatible output
│   └── gitlab-wiki/    # GitLab wiki format
├── rust/              # Future: Rust support
└── javascript/        # Future: JS/TS support
```

## Core features

**Frontmatter-driven generation**:
Users create markdown files with YAML frontmatter:
```markdown
---
template: "python/gitlab-wiki/module.md.jinja2"
griffe_target: "mypackage.utils"
griffe_options:
  include_private: false
  show_source: true
output:
  filename: "api-utils.md"
custom_vars:
  emoji: "🗄️"
  category: "Core"
---
```

**CLI commands**:
- `griffonner generate docs/pages/` - Generate all files
- `griffonner generate docs/pages/api.md` - Generate single file
- `griffonner watch docs/pages/` - Watch mode for development
- `griffonner templates` - List available templates

## Design principles

1. **Zero opinions** - No assumptions about output format or structure
2. **Template-first** - Templates control everything, rich context from Griffe
3. **Composable** - Mix generated with hand-written content
4. **Format agnostic** - Generate Markdown, RST, HTML, JSON, anything
5. **Extensible** - Plugin system and template ecosystem

## Development status

**Current state**: Basic stub implementation with placeholder main() function

**MVP Phase 1 (Core)** - Not yet implemented:
- [ ] Griffe integration
- [ ] Jinja2 templating  
- [ ] Frontmatter parsing
- [ ] Basic CLI with Typer
- [ ] File generation

**Phase 2 (Usability)** - Planned:
- [ ] Template discovery
- [ ] Watch mode
- [ ] Error handling
- [ ] Documentation
- [ ] Example templates

**Phase 3 (Ecosystem)** - Future:
- [ ] Plugin system
- [ ] Template sharing
- [ ] Performance optimisation
- [ ] Advanced CLI features