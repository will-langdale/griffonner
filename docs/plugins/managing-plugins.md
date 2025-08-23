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

Griffonner discovers plugins through Python entry points in three groups:

- `griffonner.processors` - Individual processor plugins
- `griffonner.filters` - Individual filter plugins  
- `griffonner.bundles` - Bundle plugins (contain multiple components)

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

## See also

- [Using processors](using-processors.md) - Transform Griffe objects
- [Using filters](using-filters.md) - Custom template filters  
- [Plugin development](../development/plugin-development.md) - Create plugins
- [Bundle development](../development/bundle-development.md) - Create bundles