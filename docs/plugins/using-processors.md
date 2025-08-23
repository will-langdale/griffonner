# Using processors

Processors are middleware components that intercept and transform Griffe objects before they reach your templates. They allow you to add custom metadata, modify object properties, or enrich the data available to your templates.

## What processors do

Processors run between the Griffe parsing phase and template rendering, giving you a chance to:

- Add computed metadata (complexity scores, category classifications)
- Transform or filter object properties 
- Enrich context with external data
- Modify object structure or content

**Flow**: Python Code → Griffe Parser → **Processors** → Template Engine → Output

## Basic usage

Enable processors in your frontmatter using the `processors` section:

```yaml
---
template: "python/default/module.md.jinja2"
griffe_target: "mypackage.utils"
processors:
  enabled: ["complexity_analyser", "doc_linker"]
output:
  - filename: "utils.md"
    griffe_target: "mypackage.utils"
---
```

## Configuration options

### Enabled processors

Specify exactly which processors to run:

```yaml
processors:
  enabled: ["processor_one", "processor_two"]
```

### Disabled processors

Run all available processors except specific ones:

```yaml
processors:
  disabled: ["slow_processor", "debug_processor"]
```

### Processor configuration

Pass configuration to processors:

```yaml
processors:
  enabled: ["complexity_analyser"]
  config:
    complexity_threshold: 15
    include_metrics: ["cyclomatic", "halstead"]
```

The configuration is available to processors via `context["processor_config"]`.

## Execution order

Processors run in priority order (lower numbers first):

- Priority 50: Early processors (pre-processing)
- Priority 100: Default processors (standard processing)
- Priority 150: Late processors (post-processing)

Multiple processors at the same priority level run in alphabetical order by name.

## Available processors

List all available processors:

```shell
griffonner plugins
```

This shows:

- **Processors**: Middleware components for object transformation
- **Filters**: Template filters from the same plugins
- **Bundles**: Collections of processors, filters, and templates

## Installing processors

Processors are distributed as Python packages with entry points:

```shell
# Example packages (aspirational - not yet available)
pip install griffonner-complexity-analyser
pip install griffonner-doc-linker
```

After installation, they're automatically discovered by Griffonner.

## Examples

### Documentation linker

```yaml
---
template: "python/default/module.md.jinja2" 
griffe_target: "mypackage.core"
processors:
  enabled: ["doc_linker"]
  config:
    base_url: "https://docs.example.com"
    link_external: true
---
```

The processor adds `doc_links` to your template context:

```jinja2
## Functions

{% for name, func in obj.functions.items() %}
### {{ func.name }}

{{ func.docstring.summary }}

{% if doc_links and doc_links[func.name] %}
[View full documentation]({{ doc_links[func.name] }})
{% endif %}
{% endfor %}
```

### Complexity analyser

```yaml
---
processors:
  enabled: ["complexity_analyser"]
  config:
    threshold: 10
    show_warnings: true
---
```

Adds complexity data to context:

```jinja2
## Functions

{% for name, func in obj.functions.items() %}
### {{ func.name }}

{% if complexity and complexity[func.name] %}
**Complexity**: {{ complexity[func.name].score }}
{% if complexity[func.name].score > 10 %}
⚠️ High complexity function
{% endif %}
{% endif %}
{% endfor %}
```

## Troubleshooting

### Processor not found

```
❌ Processor 'missing_processor' not found
```

- Check the processor is installed: `pip list | grep griffonner`
- List available processors: `griffonner plugins`
- Check spelling in frontmatter

### Processor failed

```
❌ Processor 'complexity_analyser' failed: Missing required config 'threshold'
```

- Check processor documentation for required configuration
- Add missing config to frontmatter `processors.config`
- Ensure config values are correct type (string, number, boolean)

### No processors running

If no `processors` section is in frontmatter, all available processors run by default. To disable all processors:

```yaml
processors:
  enabled: []  # Empty list = no processors
```

## See also

- [Managing plugins](managing-plugins.md) - Installing and discovering plugins
- [Using filters](using-filters.md) - Custom template filters
- [Plugin development](../development/plugin-development.md) - Creating your own processors