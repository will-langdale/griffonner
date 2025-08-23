# Bundle development

Create comprehensive plugin bundles that combine processors, filters, and templates for complete documentation workflows. Bundles make it easy for users to install and use related functionality together.

## What are bundles

Bundles package related documentation tools into a single installable unit:

- **Processors**: Custom data transformation and analysis
- **Filters**: Template formatting and rendering helpers  
- **Templates**: Complete template sets for specific outputs
- **Configuration**: Default settings and workflows

Example: A GitLab wiki bundle might include:
- Processors for sidebar generation and link analysis
- Filters for GitLab-specific markdown formatting
- Templates optimised for GitLab wiki display
- Default configuration for wiki workflows

## Bundle architecture

Bundles implement the `BundleProtocol` or inherit from `BaseBundle`:

```python
from griffonner.plugins import BaseBundle
from typing import Dict, List
from .processors import SidebarProcessor, LinkProcessor
from .filters import gitlab_links, wiki_format

class GitLabWikiBundle(BaseBundle):
    @property
    def name(self) -> str:
        return "gitlab-wiki"
    
    @property
    def version(self) -> str:
        return "1.2.0"
    
    @property
    def description(self) -> str:
        return "Complete GitLab wiki documentation bundle"
    
    def get_processors(self) -> Dict[str, Any]:
        """Return processors provided by this bundle."""
        return {
            "sidebar_generator": SidebarProcessor(),
            "link_analyser": LinkProcessor(),
        }
    
    def get_filters(self) -> Dict[str, Any]:
        """Return filters provided by this bundle."""
        return {
            "gitlab_links": gitlab_links,
            "wiki_format": wiki_format,
        }
    
    def get_template_paths(self) -> List[str]:
        """Return template directory paths."""
        return ["templates/gitlab-wiki/"]
```

## Creating bundle components

### Bundle processors

Create processors specific to your bundle's workflow:

```python
# processors.py
from griffonner.plugins import BaseProcessor

class SidebarProcessor(BaseProcessor):
    @property
    def name(self) -> str:
        return "sidebar_generator"
    
    @property
    def priority(self) -> int:
        return 150  # Run after main processing
    
    def process(self, griffe_obj, context):
        """Generate sidebar navigation for GitLab wiki."""
        sidebar_data = self.generate_sidebar(griffe_obj, context)
        context["sidebar"] = sidebar_data
        return griffe_obj, context
    
    def generate_sidebar(self, obj, context):
        """Build hierarchical sidebar structure."""
        config = context.get("processor_config", {})
        max_depth = config.get("sidebar_max_depth", 3)
        
        sidebar = {
            "title": obj.name,
            "sections": []
        }
        
        # Build sections from object structure
        for name, member in obj.members.items():
            if member.kind.value in ["class", "function"]:
                sidebar["sections"].append({
                    "name": name,
                    "link": f"#{name.lower().replace('_', '-')}",
                    "type": member.kind.value
                })
        
        return sidebar

class LinkProcessor(BaseProcessor):
    @property
    def name(self) -> str:
        return "link_analyser"
    
    def process(self, griffe_obj, context):
        """Analyse and enhance links for GitLab wiki."""
        links = self.extract_links(griffe_obj)
        context["doc_links"] = links
        return griffe_obj, context
    
    def extract_links(self, obj):
        """Extract documentation links from docstrings."""
        links = {}
        
        if obj.docstring:
            # Extract URLs from docstring
            import re
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', obj.docstring.description or "")
            if urls:
                links[obj.name] = urls[0]  # First URL found
        
        # Process member objects recursively
        for name, member in getattr(obj, 'members', {}).items():
            member_links = self.extract_links(member)
            links.update(member_links)
        
        return links
```

### Bundle filters

Create filters that work together for consistent formatting:

```python
# filters.py
import re

def gitlab_links(text):
    """Convert markdown links to GitLab wiki format."""
    if not text:
        return text
    
    # Convert [text](url) to [[url | text]]
    def replace_link(match):
        text = match.group(1)
        url = match.group(2)
        
        # Handle relative links
        if url.startswith('#'):
            return f"[[#{url[1:]} | {text}]]"
        elif not url.startswith(('http', '/')):
            return f"[[{url} | {text}]]"
        else:
            return f"[{text}]({url})"  # Keep external links as-is
    
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    return re.sub(pattern, replace_link, text)

def wiki_format(text):
    """Apply GitLab wiki-specific formatting."""
    if not text:
        return text
    
    # Convert emphasis
    text = text.replace("**", "'''")  # Bold
    text = text.replace("*", "''")    # Italic
    
    # Convert code blocks
    text = re.sub(r'```(\w+)?\n(.*?)\n```', r'```\1\n\2\n```', text, flags=re.DOTALL)
    
    # Convert inline code
    text = re.sub(r'`([^`]+)`', r'`\1`', text)
    
    return text

def format_signature(signature_obj):
    """Format function signatures for wiki display."""
    if not signature_obj or not hasattr(signature_obj, 'parameters'):
        return str(signature_obj)
    
    params = []
    for param in signature_obj.parameters:
        param_str = f"**{param.name}**"
        
        if param.annotation:
            param_str += f": `{param.annotation}`"
        
        if param.default:
            param_str += f" = `{param.default}`"
            
        params.append(param_str)
    
    if len(params) <= 2:
        return f"({', '.join(params)})"
    
    return f"(\n  {',\n  '.join(params)}\n)"

def type_badge(kind_str):
    """Generate type badges for objects."""
    badges = {
        "module": "📦",
        "class": "🏗️", 
        "function": "⚙️",
        "method": "🔧",
        "property": "📋",
    }
    
    icon = badges.get(kind_str, "❓")
    return f"{icon} {kind_str.title()}"
```

### Bundle templates

Create templates optimised for your bundle's output format:

```jinja2
{# templates/gitlab-wiki/module.md.jinja2 #}
# {{ obj.name }} {{ obj.kind | type_badge }}

{{ obj.docstring.summary | gitlab_links if obj.docstring }}

{% if obj.docstring and obj.docstring.description %}
## Description

{{ obj.docstring.description | gitlab_links | wiki_format }}
{% endif %}

{% if sidebar and sidebar.sections %}
## Contents

{% for section in sidebar.sections %}
- [{{ section.name }}]({{ section.link }}) {{ section.type | type_badge }}
{% endfor %}
{% endif %}

{% set functions = [] %}
{% set classes = [] %}
{% for name, member in obj.members.items() %}
  {% if member.kind.value == "function" %}
    {% set _ = functions.append((name, member)) %}
  {% elif member.kind.value == "class" %}
    {% set _ = classes.append((name, member)) %}
  {% endif %}
{% endfor %}

{% if functions %}
## Functions

{% for name, func in functions %}
### {{ func.name }} ⚙️

{{ func.docstring.summary | gitlab_links if func.docstring }}

{% if func.signature %}
**Signature**: {{ func.signature | format_signature }}
{% endif %}

{% if func.docstring and func.docstring.description %}
{{ func.docstring.description | gitlab_links | wiki_format }}
{% endif %}

{% if doc_links and doc_links[name] %}
📖 [Full documentation]({{ doc_links[name] }})
{% endif %}

---
{% endfor %}
{% endif %}

{% if classes %}
## Classes

{% for name, cls in classes %}
### {{ cls.name }} 🏗️

{{ cls.docstring.summary | gitlab_links if cls.docstring }}

{% if cls.docstring and cls.docstring.description %}
{{ cls.docstring.description | gitlab_links | wiki_format }}
{% endif %}

{% set methods = [] %}
{% for method_name, method in cls.members.items() %}
  {% if method.kind.value == "function" and not method_name.startswith('_') %}
    {% set _ = methods.append((method_name, method)) %}
  {% endif %}
{% endfor %}

{% if methods %}
#### Methods

{% for method_name, method in methods %}
##### `{{ method.name }}` 🔧

{{ method.docstring.summary | gitlab_links if method.docstring }}

{% if method.signature %}
**Signature**: {{ method.signature | format_signature }}
{% endif %}
{% endfor %}
{% endif %}

---
{% endfor %}
{% endif %}

{% if custom_vars.footer %}
---
{{ custom_vars.footer | gitlab_links | wiki_format }}
{% endif %}

*Generated with Griffonner GitLab Wiki Bundle v{{ bundle_version }}*
```

## Bundle configuration

### Default configuration

Provide sensible defaults in your bundle:

```python
class GitLabWikiBundle(BaseBundle):
    def get_default_config(self) -> Dict[str, Any]:
        """Default configuration for GitLab wiki generation."""
        return {
            "processors": {
                "enabled": ["sidebar_generator", "link_analyser"],
                "config": {
                    "sidebar_max_depth": 3,
                    "include_private": False,
                    "generate_toc": True
                }
            },
            "template_defaults": {
                "bundle_version": self.version,
                "wiki_style": "compact"
            }
        }
    
    def apply_defaults(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with bundle defaults."""
        defaults = self.get_default_config()
        
        # Deep merge configuration
        def merge_dict(base, override):
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_dict(result[key], value)
                else:
                    result[key] = value
            return result
        
        return merge_dict(defaults, user_config)
```

### Template discovery

Bundles can include multiple template sets:

```
my-bundle/
├── templates/
│   └── gitlab-wiki/
│       ├── module.md.jinja2
│       ├── class.md.jinja2
│       ├── function.md.jinja2
│       └── api-index.md.jinja2
├── my_bundle/
│   ├── __init__.py
│   ├── processors.py
│   └── filters.py
└── pyproject.toml
```

```python
def get_template_paths(self) -> List[str]:
    """Template paths relative to package root."""
    return [
        "templates/gitlab-wiki/",
    ]

def get_template_sets(self) -> Dict[str, List[str]]:
    """Named template sets for different use cases."""
    return {
        "default": ["module.md.jinja2", "class.md.jinja2"],
        "comprehensive": ["module.md.jinja2", "class.md.jinja2", "function.md.jinja2"],
        "api-only": ["api-index.md.jinja2"],
    }
```

## Complete bundle example

### Package structure

```
griffonner-gitlab-wiki/
├── griffonner_gitlab_wiki/
│   ├── __init__.py              # Bundle class export
│   ├── bundle.py                # GitLabWikiBundle class
│   ├── processors.py            # Bundle processors
│   └── filters.py               # Bundle filters
├── templates/
│   └── gitlab-wiki/
│       ├── module.md.jinja2
│       ├── class.md.jinja2
│       └── api-index.md.jinja2
├── tests/
│   ├── test_bundle.py
│   ├── test_processors.py
│   └── test_filters.py
├── examples/
│   └── basic-usage/
│       ├── pages/
│       │   └── api.md           # Example frontmatter
│       └── README.md
├── pyproject.toml
├── README.md
└── LICENSE
```

### Entry points configuration

```toml
# pyproject.toml
[project]
name = "griffonner-gitlab-wiki"
version = "1.2.0"
description = "GitLab wiki documentation bundle for Griffonner"
dependencies = ["griffonner>=1.0.0"]

[project.entry-points."griffonner.bundles"]
gitlab-wiki = "griffonner_gitlab_wiki:GitLabWikiBundle"

# Optional: Direct access to components
[project.entry-points."griffonner.processors"]
sidebar_generator = "griffonner_gitlab_wiki.processors:SidebarProcessor"
link_analyser = "griffonner_gitlab_wiki.processors:LinkProcessor"

[project.entry-points."griffonner.filters"]
gitlab_links = "griffonner_gitlab_wiki.filters:gitlab_links"
wiki_format = "griffonner_gitlab_wiki.filters:wiki_format"
```

### Bundle usage

Users install and use the complete bundle:

```shell
# Install bundle (example - not yet available)
pip install griffonner-gitlab-wiki

# Check bundle contents
griffonner bundle gitlab-wiki

# Use in documentation
```

```yaml
# docs/pages/api.md
---
template: "gitlab-wiki/module.md.jinja2"
griffe_target: "myproject.api"
processors:
  enabled: ["gitlab-wiki.sidebar_generator", "gitlab-wiki.link_analyser"]
  config:
    sidebar_max_depth: 2
    include_toc: true
output:
  - filename: "API-Reference.md"
    griffe_target: "myproject.api"
custom_vars:
  footer: "See [[Development Guide]] for contributing information."
---

# API Reference

This page documents the main API for MyProject.
```

## Testing bundles

### Bundle testing

```python
# tests/test_bundle.py
import pytest
from griffonner_gitlab_wiki import GitLabWikiBundle

def test_bundle_creation():
    bundle = GitLabWikiBundle()
    
    assert bundle.name == "gitlab-wiki"
    assert bundle.version == "1.2.0"
    assert "GitLab wiki" in bundle.description

def test_bundle_components():
    bundle = GitLabWikiBundle()
    
    processors = bundle.get_processors()
    assert "sidebar_generator" in processors
    assert "link_analyser" in processors
    
    filters = bundle.get_filters()
    assert "gitlab_links" in filters
    assert "wiki_format" in filters
    
    template_paths = bundle.get_template_paths()
    assert "templates/gitlab-wiki/" in template_paths

def test_bundle_integration():
    """Test bundle works with actual Griffonner generation."""
    from griffonner.plugins.manager import PluginManager
    
    manager = PluginManager()
    
    # Manually register bundle for testing
    bundle = GitLabWikiBundle()
    manager._bundles["gitlab-wiki"] = bundle
    
    # Check processors are available
    processors = manager.get_processors()
    assert "gitlab-wiki.sidebar_generator" in processors
    
    # Check filters are available
    filters = manager.get_filters()
    assert "gitlab-wiki.gitlab_links" in filters
```

### Integration testing

```python
# tests/test_integration.py
import tempfile
from pathlib import Path
from griffonner.core import generate

def test_full_generation():
    """Test complete generation workflow with bundle."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test frontmatter file
        pages_dir = tmpdir / "pages"
        pages_dir.mkdir()
        
        test_page = pages_dir / "test.md"
        test_page.write_text("""---
template: "gitlab-wiki/module.md.jinja2"
output:
  - filename: "test-output.md"
    griffe_target: "json"
processors:
  enabled: ["gitlab-wiki.sidebar_generator"]
---

Test content
""")
        
        output_dir = tmpdir / "output"
        
        # Run generation
        result = generate(pages_dir, output_dir)
        
        assert len(result) == 1
        output_file = output_dir / "pages" / "test-output.md"
        assert output_file.exists()
        
        content = output_file.read_text()
        assert "json 📦" in content  # Type badge from filter
        assert "## Contents" in content  # Sidebar from processor
```

## Publishing bundles

### Documentation

Include comprehensive documentation:

```markdown
# GitLab Wiki Bundle for Griffonner

Complete documentation bundle for generating GitLab wiki-compatible markdown.

## Features

- **Sidebar generation**: Automatic navigation sidebars
- **Link formatting**: Convert markdown links to GitLab wiki format
- **Type badges**: Visual indicators for functions, classes, modules
- **Wiki-specific formatting**: Optimised for GitLab wiki rendering

## Installation

```shell
# Example - not yet available
pip install griffonner-gitlab-wiki
```

## Quick start

Create a frontmatter file:

```yaml
---
template: "gitlab-wiki/module.md.jinja2"
griffe_target: "mypackage"
processors:
  enabled: ["gitlab-wiki.sidebar_generator"]
output:
  - filename: "API.md"
    griffe_target: "mypackage"
---
```

Generate documentation:

```shell
griffonner generate docs/pages/ --output wiki/
```

## Configuration

All processors support configuration via frontmatter:

```yaml
processors:
  config:
    sidebar_max_depth: 3      # Maximum sidebar nesting
    include_private: false    # Include private members
    generate_toc: true       # Generate table of contents
```

## Templates

- `module.md.jinja2` - Complete module documentation
- `class.md.jinja2` - Class-focused documentation  
- `api-index.md.jinja2` - API overview page
```

### PyPI publishing

```shell
# Build and publish
python -m build
python -m twine upload dist/*
```

## Best practices

### Bundle design

- **Cohesive functionality**: Bundle related features together
- **Clear naming**: Use descriptive, consistent names
- **Flexible configuration**: Allow users to customise behaviour
- **Documentation**: Provide clear examples and configuration guides

### Version management

```python
# Use semantic versioning
__version__ = "1.2.0"

class GitLabWikiBundle(BaseBundle):
    @property
    def version(self) -> str:
        return __version__
```

### Backwards compatibility

- Maintain stable APIs between versions
- Deprecate features before removing them
- Document breaking changes clearly

### Template organisation

```
templates/
└── bundle-name/
    ├── module.md.jinja2      # Main templates
    ├── class.md.jinja2
    ├── partials/             # Reusable components
    │   ├── signature.jinja2
    │   └── docstring.jinja2
    └── layouts/              # Base layouts
        └── wiki-base.jinja2
```

## See also

- [Plugin development](plugin-development.md) - Creating individual plugins
- [Using processors](../plugins/using-processors.md) - How processors work
- [Using filters](../plugins/using-filters.md) - How filters work
- [AI bundle creation](ai-bundle-creation.md) - AI assistant for bundle development