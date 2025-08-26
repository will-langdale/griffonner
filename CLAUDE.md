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

## Architecture

**Current package structure**:
```
src/griffonner/
├── cli.py              # Typer-based CLI
├── core.py             # Main generation logic
├── frontmatter.py      # YAML frontmatter parsing
├── templates.py        # Template discovery & loading
├── griffe_wrapper.py   # Griffe integration
├── watcher.py          # Watch mode implementation
└── plugins/            # Plugin system (Phase 3)
    ├── __init__.py
    ├── protocols.py    # Plugin interface definitions
    ├── base.py         # Base classes for plugins
    └── manager.py      # Plugin discovery & management
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
- `griffonner generate --local-plugins <module>` - Generate with local plugins
- `griffonner watch docs/pages/` - Watch mode for development
- `griffonner templates` - List available templates
- `griffonner plugins` - List all available plugins
- `griffonner bundle <name>` - Show details about a specific bundle

## Design principles

1. **Zero opinions** - No assumptions about output format or structure
2. **Template-first** - Templates control everything, rich context from Griffe
3. **Composable** - Mix generated with hand-written content
4. **Format agnostic** - Generate Markdown, RST, HTML, JSON, anything
5. **Extensible** - Plugin system and template ecosystem

## Development status

**Current state**: Full MVP Phase 1 implementation complete with working CLI

**MVP Phase 1 (Core)** - ✅ Complete:
- [x] Griffe integration
- [x] Jinja2 templating  
- [x] Frontmatter parsing
- [x] Basic CLI with Typer
- [x] File generation

**Phase 2 (Usability)** - ✅ Complete:
- [x] Template discovery
- [x] Watch mode
- [x] Error handling
- [x] Documentation

**Phase 3 (Ecosystem)** - ✅ Complete:
- [x] Plugin system with processors and filters
- [x] Template bundle system
- [x] Entry points discovery
- [x] CLI plugin management

**Phase 4 (Future)**:
- [ ] Template sharing marketplace
- [ ] Performance optimisation
- [ ] Advanced CLI features

## Plugin System (Phase 3)

Griffonner now supports a comprehensive plugin system that allows extending functionality through:

### Processors
Middleware components that intercept and transform Griffe objects before templating:

```python
from griffonner.plugins import BaseProcessor

class MyProcessor(BaseProcessor):
    @property
    def name(self) -> str:
        return "my_processor"
    
    @property  
    def priority(self) -> int:
        return 75  # Lower = runs earlier
    
    def process(self, griffe_obj, context):
        # Add custom metadata
        context["my_data"] = analyse_object(griffe_obj)
        return griffe_obj, context
```

### Filters
Custom Jinja2 template filters for data transformation:

```python
def format_signature(signature_str):
    """Format function signatures nicely"""
    return signature_str.replace("(", "(\n    ").replace(", ", ",\n    ")

# Use in templates: {{ func.signature | format_signature }}
```

### Bundles
Collections of processors, filters, and templates packaged together:

```python
from griffonner.plugins import BaseBundle

class GitLabWikiBundle(BaseBundle):
    @property
    def name(self) -> str:
        return "gitlab-wiki"
    
    def get_processors(self):
        return {"sidebar": SidebarProcessor()}
    
    def get_filters(self):
        return {"gitlab_link": format_gitlab_links}
    
    def get_template_paths(self):
        return ["templates/gitlab-wiki/"]
```

### Entry Points Registration
Plugins are discovered via setuptools entry points:

```python
# In setup.py or pyproject.toml
entry_points={
    "griffonner.processors": [
        "my_processor = mypackage:MyProcessor",
    ],
    "griffonner.filters": [
        "format_signature = mypackage.filters:format_signature",
    ],
    "griffonner.bundles": [
        "gitlab-wiki = mypackage:GitLabWikiBundle",
    ],
}
```

### Local Plugin Modules
Local plugins allow loading project-specific filters and processors from Python modules using `--local-plugins <module_name>`. Implementation uses `importlib.import_module()` for clean module-based discovery without filesystem scanning or sys.path manipulation.

**Architecture:**
- PluginManager accepts `local_plugin_modules` parameter in constructor
- Filters: Any callable function at module level (excluding private `_` names)  
- Processors: Classes with `process` method (duck typing or BaseProcessor inheritance)
- Name registration: Both simple (`filter_name`) and qualified (`module.filter_name`) names
- Integration: Works alongside existing entry point plugin system

See `docs/plugins/managing-plugins.md` for usage examples and `docs/user-guide/cli-reference.md` for CLI options.

### Frontmatter Configuration
Control processor execution per file:

```yaml
---
template: "python/default/module.md.jinja2"
griffe_target: "mypackage.utils"
processors:
  enabled: ["complexity_analyser", "doc_linker"]  # Only run these
  # OR
  disabled: ["slow_processor"]  # Run all except these
  config:
    complexity_threshold: 10
output:
  filename: "api-utils.md"
---
```

### Available CLI Commands
- `griffonner plugins` - List all processors, filters, and bundles
- `griffonner bundle <name>` - Show bundle details and components

This plugin system enables the creation of community packages like `griffonner-gitlab-wiki` or `griffonner-sphinx-compat` that bundle templates, processors, and filters for specific documentation workflows.