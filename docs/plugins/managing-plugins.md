# Managing plugins

Griffonner's plugin system extends functionality through processors, filters, and template bundles. This guide covers discovering, installing, and managing plugins in your documentation workflow.

## Plugin system overview

Griffonner plugins provide three types of extensions:

- **Processors**: Transform Griffe objects before template rendering
- **Filters**: Add custom Jinja2 template filters for data formatting
- **Bundles**: Collections of processors, filters, and templates for specific workflows

Plugins are discovered automatically using Python's entry points system.

## Discovering plugins

### List all plugins

```shell
griffonner plugins
```

Shows all available plugins:

```
🔌 Available plugins:

📋 Processors:
  - complexity_analyser
  - doc_linker
  - gitlab-wiki.sidebar_generator

🔧 Filters:
  - format_signature
  - complexity_badge
  - gitlab-wiki.gitlab_links

📦 Bundles:
  - gitlab-wiki
```

### Bundle details

Get detailed information about a specific bundle:

```shell
griffonner bundle gitlab-wiki
```

Shows bundle contents:

```
📦 Bundle: gitlab-wiki
   Version: 1.2.0
   Description: Complete GitLab wiki documentation bundle

   📋 Processors:
     - sidebar_generator

   🔧 Filters:
     - gitlab_links
     - wiki_format

   📄 Template paths:
     - templates/gitlab-wiki/
```

## Installing plugins

Plugins are regular Python packages with entry points configuration. Install via pip:

```shell
# Install from PyPI (example packages - not yet available)
pip install griffonner-gitlab-wiki
pip install griffonner-complexity-analyser

# Install from Git repository
pip install git+https://github.com/user/griffonner-custom-plugin.git

# Install in development mode
cd my-plugin/
pip install -e .
```

After installation, plugins are automatically discovered on the next Griffonner run.

## Plugin discovery

Griffonner discovers plugins through two mechanisms:

### Entry points (installed packages)

Discovered automatically through Python entry points in three groups:

- `griffonner.processors` - Individual processor plugins
- `griffonner.filters` - Individual filter plugins  
- `griffonner.bundles` - Bundle plugins (contain multiple components)

### Local plugin modules

Loaded directly from Python modules you specify using the `--local-plugins` option.

### Entry points example

In a plugin's `pyproject.toml`:

```toml
[project.entry-points."griffonner.processors"]
complexity_analyser = "mypackage:ComplexityProcessor"

[project.entry-points."griffonner.filters"] 
format_signature = "mypackage.filters:format_signature"

[project.entry-points."griffonner.bundles"]
gitlab-wiki = "mypackage:GitLabWikiBundle"
```

## Local plugin modules

Local plugins allow you to define custom filters and processors without creating separate packages. This is perfect for project-specific functionality or quick customisations.

### Creating local plugins

Create a Python module anywhere in your project:

```python
# myproject/docs_plugins.py
"""Custom documentation plugins for MyProject."""

from typing import Any, Dict, Tuple, Union
from griffe import Alias, Object as GriffeObject
from griffonner.plugins.base import BaseProcessor

# Custom filters (regular functions)
def emphasise_name(name: str) -> str:
    """Add emphasis formatting to names."""
    return f"**{name}**"

def format_params(params: str) -> str:
    """Format parameter lists nicely."""
    return params.replace(", ", ",\n    ")

# Custom processors (classes with process method)
class ProjectMetadata(BaseProcessor):
    """Adds project-specific metadata to context."""
    
    @property
    def name(self) -> str:
        return "project_metadata"
    
    @property
    def priority(self) -> int:
        return 50  # Run early
    
    def process(
        self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
    ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        # Add custom metadata
        context["project"] = {
            "name": "MyProject",
            "version": "2.1.0",
            "base_url": "https://myproject.example.com"
        }
        
        # Add object-specific data
        obj_name = getattr(griffe_obj, "name", "unknown")
        context["api_url"] = f"{context['project']['base_url']}/api/{obj_name}"
        
        return griffe_obj, context

class ComplexityAnalyser:
    """Analyser without inheriting from BaseProcessor."""
    
    @property
    def name(self) -> str:
        return "complexity_analyser"
    
    def process(self, griffe_obj, context):
        # Calculate complexity metrics
        context["complexity"] = self._analyse_complexity(griffe_obj)
        return griffe_obj, context
    
    def _analyse_complexity(self, obj):
        # Simplified complexity calculation
        return {"score": 3, "level": "low"}

# Private items are ignored
def _private_helper():
    """This won't be loaded as a filter."""
    pass
```

### Using local plugins

Specify your module with the `--local-plugins` option:

```shell
# Single module
griffonner generate docs/pages/ --local-plugins myproject.docs_plugins

# Multiple modules  
griffonner generate docs/pages/ \
  --local-plugins myproject.filters \
  --local-plugins myproject.processors

# With other options
griffonner generate docs/pages/ \
  --output build/docs \
  --local-plugins myproject.docs_plugins \
  --template-dir custom-templates/
```

### Plugin naming

Local plugins get two names for flexibility:

- **Simple name**: `emphasise_name`, `project_metadata`
- **Qualified name**: `myproject.docs_plugins.emphasise_name`, `myproject.docs_plugins.project_metadata`

Use qualified names to avoid conflicts with installed plugins or other modules.

### Using in templates

Local filters work exactly like installed ones:

```jinja2
# {{ obj.name | emphasise_name }}

{% for func in obj.functions %}
## {{ func.name | emphasise_name }}

{{ func.docstring.summary }}

**Signature**: {{ func.signature | format_params }}

**API URL**: {{ api_url }}
{% endfor %}

Project: {{ project.name }} v{{ project.version }}
```

### Using in frontmatter

Control local processors like any others:

```yaml
---
template: "python/default/module.md.jinja2"
griffe_target: "myproject.core"

# Use local processors
processors:
  enabled: ["project_metadata", "complexity_analyser"]
  config:
    complexity_threshold: 5

output:
  - filename: "core-api.md"
    griffe_target: "myproject.core"
---
```

### Name conflict resolution

If multiple modules provide the same filter or processor name:

```shell
griffonner plugins --local-plugins mod1.plugins --local-plugins mod2.plugins
```

Shows:

```
🔧 Filters:
  - format_text                    # From first module loaded (mod1)
  - mod1.plugins.format_text       # Qualified name always available
  - mod2.plugins.format_text       # Qualified name always available
```

**Resolution rules**:
- First loaded module gets the simple name
- All modules get qualified names
- Use qualified names to access specific versions

### Module requirements

Your local plugin module must:

- Be importable from your current Python environment
- Contain callable functions for filters
- Contain classes with `process` methods for processors
- Avoid private names (starting with `_`)

**Processors** can either:
- Inherit from `BaseProcessor` (recommended)
- Implement duck typing with `name` property and `process` method

## Using plugins

### In frontmatter

Control processor execution in your documentation files:

```yaml
---
template: "python/default/module.md.jinja2"
griffe_target: "mypackage.core"
processors:
  enabled: ["complexity_analyser", "doc_linker"]
  config:
    complexity_threshold: 10
    base_url: "https://docs.example.com"
output:
  - filename: "core.md"
    griffe_target: "mypackage.core"
---
```

### In templates

Use filters directly in your templates:

```jinja2
# {{ obj.name }}

{% for func in obj.functions %}
## {{ func.name }}

{{ func.docstring.summary }}

**Signature**: {{ func.signature | format_signature }}

{% if complexity[func.name] %}
**Complexity**: {{ complexity[func.name] | complexity_badge }}
{% endif %}
{% endfor %}
```

## Community plugins

### Finding plugins

Common places to find Griffonner plugins:

- PyPI: Search for packages starting with "griffonner-"
- GitHub: Search for "griffonner plugin" or "griffonner bundle"
- Documentation: Check plugin lists in community resources

### Popular plugin types

- **Format converters**: Markdown to HTML, reStructuredText, etc.
- **Documentation enhancers**: Complexity analysis, link generation
- **Platform integrations**: GitLab wiki, Confluence, Notion
- **Code analysers**: Test coverage, dependency tracking
- **Styling**: Badges, icons, formatting helpers

## Troubleshooting

### Plugin not loading

```shell
griffonner plugins
# Plugin not in list
```

**Solutions**:

- Verify installation: `pip list | grep griffonner`
- Check entry points: Look at package metadata
- Reinstall plugin: `pip uninstall package && pip install package`

### Import errors

```
❌ Failed to load plugin 'my_processor': No module named 'mypackage'
```

**Solutions**:

- Check plugin dependencies: `pip install -r requirements.txt`
- Verify Python path includes plugin location
- Check for conflicting package versions

### Local plugin issues

**Module not found**:
```
❌ Failed to import module myproject.docs_plugins: No module named 'myproject'
```

**Solutions**:
- Ensure module is in your Python path
- Use absolute imports: `myproject.docs_plugins` not `docs_plugins`
- Check current working directory includes your project root
- Verify module has `__init__.py` files if it's a package

**Functions not loaded as filters**:
```shell
griffonner plugins --local-plugins mymodule
# Expected filter missing from list
```

**Solutions**:
- Ensure functions are at module level (not inside classes)
- Check function names don't start with `_`
- Verify functions are callable (not variables)
- Import dependencies inside functions if needed

**Processors not instantiated**:
```
❌ Failed to instantiate processor MyProcessor: TypeError
```

**Solutions**:
- Ensure processor class has no required `__init__` parameters
- Check processor has `process` method
- Add `name` property if using duck typing (not inheriting from `BaseProcessor`)
- Verify all imports are available

### Plugin conflicts

If multiple plugins provide the same processor or filter name:

```shell
griffonner plugins
# Look for duplicate names
```

**Solutions**:

- Remove unused plugins: `pip uninstall unwanted-plugin`
- Use bundle-specific names when possible
- Check plugin documentation for namespace options

### Performance issues

If plugins slow down generation:

```yaml
# Disable slow processors
processors:
  disabled: ["slow_processor"]

# Or enable only essential ones
processors:
  enabled: ["essential_processor"]
```

## Plugin development

Want to create your own plugins? See:

- [Plugin development](../development/plugin-development.md) - Creating processors and filters
- [Bundle development](../development/bundle-development.md) - Creating template bundles

## Examples

### Documentation workflow

```yaml
# docs/pages/api.md
---
template: "gitlab-wiki/module.md.jinja2"
griffe_target: "myproject.api"
processors:
  enabled: ["complexity_analyser", "gitlab-wiki.sidebar_generator"]
  config:
    complexity_threshold: 8
    sidebar_max_depth: 3
output:
  - filename: "API-Reference.md"
    griffe_target: "myproject.api"
---
```

Template uses both processors and filters:

```jinja2
# {{ obj.name }} API

{{ obj.docstring.summary | gitlab_emphasis }}

{% for func in obj.functions %}
## {{ func.name | code_format }}

{{ func.docstring.description | gitlab_links }}

{% if complexity[func.name] %}
{{ complexity[func.name] | complexity_badge }}
{% endif %}

**Signature**: {{ func.signature | format_signature | code_block }}
{% endfor %}
```

### Bundle installation workflow

```shell
# Install a complete documentation bundle (example - not yet available)
pip install griffonner-gitlab-wiki

# Check what's included
griffonner bundle gitlab-wiki

# Use in your documentation
griffonner generate docs/pages/ --output wiki/
```

### Local plugins workflow

```python
# Create myproject/docs_plugins.py
def project_link(text: str) -> str:
    """Format internal project links."""
    return f"[{text}](https://myproject.example.com/docs/{text.lower()})"

class ProjectAnalyser:
    @property
    def name(self) -> str:
        return "project_analyser"
    
    def process(self, griffe_obj, context):
        context["project_info"] = {
            "component": self._get_component(griffe_obj),
            "stability": "stable"
        }
        return griffe_obj, context
    
    def _get_component(self, obj):
        return "core" if "core" in str(obj.filepath) else "utils"
```

Use in generation:

```shell
# Generate with local plugins
griffonner generate docs/pages/ --local-plugins myproject.docs_plugins

# Check loaded plugins
griffonner plugins --local-plugins myproject.docs_plugins
```

Template usage:

```jinja2
# {{ obj.name | project_link }}

{{ obj.docstring.summary }}

Component: {{ project_info.component }} ({{ project_info.stability }})

{% for method in obj.methods %}
- {{ method.name | project_link }}
{% endfor %}
```

## See also

- [Using processors](using-processors.md) - Transform Griffe objects
- [Using filters](using-filters.md) - Custom template filters  
- [Plugin development](../development/plugin-development.md) - Create plugins
- [Bundle development](../development/bundle-development.md) - Create bundles