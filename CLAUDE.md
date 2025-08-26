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
- `griffonner generate docs/pages/ --local-plugins myproject.docs_utils` - Generate with local plugins
- `griffonner generate docs/pages/ -l myproject.utils -l myproject.helpers` - Multiple local plugin modules
- `griffonner watch docs/pages/` - Watch mode for development  
- `griffonner watch docs/pages/ --local-plugins myproject.docs_utils` - Watch with local plugins
- `griffonner templates` - List available templates
- `griffonner plugins` - List all available plugins
- `griffonner plugins --local-plugins myproject.docs_utils` - List plugins including local ones
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
For project-specific plugins, you can specify Python modules containing local filters and processors via CLI. This approach allows you to keep custom documentation logic within your project without needing to package it as a separate plugin.

**CLI Usage:**
```bash
# Single module
griffonner generate docs/pages/ --local-plugins myproject.docs_utils

# Multiple modules using long form
griffonner generate docs/pages/ --local-plugins myproject.docs_utils --local-plugins myproject.helpers

# Multiple modules using short form
griffonner generate docs/pages/ -l myproject.utils -l myproject.helpers -l myproject.formatters

# Works with all commands that support plugins
griffonner watch docs/pages/ --local-plugins myproject.docs_utils
griffonner plugins --local-plugins myproject.docs_utils
```

**Local Plugin Module Structure:**
```python
# myproject/docs_utils.py
"""Custom documentation utilities for MyProject."""

def format_signature(sig):
    """Filter function - auto-registered as 'format_signature'
    
    Usage: {{ func.signature | format_signature }}
    """
    return sig.replace("(", "(\n    ").replace(", ", ",\n    ")

def prettify_name(name):
    """Convert snake_case to Title Case
    
    Usage: {{ func.name | prettify_name }}
    """
    return name.replace("_", " ").title()

def link_to_source(obj_path, line_number=None):
    """Generate source code links
    
    Usage: {{ obj | link_to_source }}
    """
    base_url = "https://github.com/myorg/myproject/blob/main"
    if line_number:
        return f"{base_url}/{obj_path}#L{line_number}"
    return f"{base_url}/{obj_path}"

class MetadataProcessor(BaseProcessor):
    """Adds custom metadata to template context"""
    
    @property
    def name(self):
        return "metadata_processor"
    
    @property
    def priority(self):
        return 75  # Run before default processors
    
    def process(self, obj, context):
        context["custom_metadata"] = {
            "processed": True,
            "complexity": self._calculate_complexity(obj),
            "tags": self._extract_tags(obj)
        }
        return obj, context
    
    def _calculate_complexity(self, obj):
        # Custom complexity calculation logic
        return len(getattr(obj, "members", {}))
    
    def _extract_tags(self, obj):
        # Extract custom tags from docstrings
        docstring = getattr(obj, "docstring", {})
        if docstring and docstring.value:
            # Simple tag extraction example
            if "@deprecated" in docstring.value:
                return ["deprecated"]
            if "@experimental" in docstring.value:
                return ["experimental"]
        return []

# Simple processor without inheriting from BaseProcessor
class SimpleDocProcessor:
    """A simple processor for basic doc enhancements"""
    
    @property
    def name(self):
        return "simple_doc_processor"
    
    def process(self, obj, context):
        # Add some simple enhancements
        context["has_examples"] = self._has_examples(obj)
        return obj, context
    
    def _has_examples(self, obj):
        docstring = getattr(obj, "docstring", {})
        if docstring and docstring.value:
            return "Example" in docstring.value or ">>> " in docstring.value
        return False
```

**Usage in Templates:**
```jinja2
{# Use local filters #}
<h2>{{ func.name | prettify_name }}</h2>
<pre>{{ func.signature | format_signature }}</pre>
<a href="{{ func | link_to_source }}">View Source</a>

{# Use context added by processors #}
{% if custom_metadata.complexity > 5 %}
<div class="complexity-warning">High complexity: {{ custom_metadata.complexity }}</div>
{% endif %}

{% for tag in custom_metadata.tags %}
<span class="tag tag-{{ tag }}">{{ tag }}</span>
{% endfor %}

{% if has_examples %}
<div class="has-examples">✓ Includes examples</div>
{% endif %}
```

**Usage in Frontmatter:**
```yaml
---
template: "python/default/module.md.jinja2"
griffe_target: "myproject.core"
processors:
  enabled: ["metadata_processor", "simple_doc_processor"]  # Use local processors
output:
  filename: "core-api.md"
custom_vars:
  show_complexity: true
---
```

**Name Resolution:**
Local plugins are registered with both simple and qualified names:
- **Simple name**: `format_signature` (if no conflict)
- **Qualified name**: `myproject.docs_utils.format_signature` (always available)

If multiple modules define the same function/processor name, the first one loaded gets the simple name, but all are accessible via qualified names.

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