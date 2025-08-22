# Templates

Griffonner uses Jinja2 templates to transform Griffe's parsed Python code into documentation. Templates give you complete control over output format and structure.

## Template types

Griffonner includes built-in templates and supports custom templates:

- **Built-in templates**: Ready-to-use templates for common documentation formats
- **Custom templates**: Create templates tailored to your specific needs
- **Community templates**: Share and reuse templates across projects

## Quick start

### Using built-in templates

List available templates:

```shell
griffonner templates
```

Use a template in frontmatter:

```yaml
---
template: "python/default/module.md.jinja2"
output:
  - filename: "api.md"
    griffe_target: "mypackage"
---
```

### Creating custom templates

Create a template file:

```jinja2
{# docs/templates/my-template.md.jinja2 #}
# {{ obj.name }}

{{ obj.docstring.summary if obj.docstring }}

## Functions

{% for name, func in obj.members.items() %}
{% if func.kind.value == "function" %}
### {{ func.name }}
{{ func.docstring.summary if func.docstring }}
{% endif %}
{% endfor %}
```

Reference it in frontmatter:

```yaml
---
template: "my-template.md.jinja2"
output:
  - filename: "output.md"
    griffe_target: "mymodule"
---
```

## Template context

Templates receive rich context from Griffe's code analysis:

- `{{ obj }}` - The parsed Python object (module, class, function)
- `{{ custom_vars }}` - Variables defined in frontmatter
- `{{ source_content }}` - Markdown content after frontmatter
- `{{ source_path }}` - Path to the source file

## Learn more

- **[Template development](template-development.md)** - Complete guide to creating templates
- **[Template reference](template-reference.md)** - Built-in templates and context variables
- **[AI template guide](ai-template-guide.md)** - Get AI assistance creating templates

## Examples

### Basic module template

```jinja2
# {{ obj.name }} module

{{ obj.docstring.summary if obj.docstring }}

{% for name, member in obj.members.items() %}
{% if member.kind.value == "function" and not name.startswith('_') %}
## {{ member.name }}
{{ member.docstring.summary if member.docstring }}
{% endif %}
{% endfor %}
```

### Class documentation template

```jinja2
# {{ obj.name }}

{{ obj.docstring.summary if obj.docstring }}

## Methods

{% for name, method in obj.members.items() %}
{% if method.kind.value == "function" and not name.startswith('_') %}
### {{ method.name }}
{{ method.docstring.summary if method.docstring }}
{% endif %}
{% endfor %}
```

### Custom format template

````jinja2
---
title: {{ obj.name }}
type: {{ obj.kind.value }}
---

# {{ custom_vars.title or obj.name }}

> Generated from `{{ griffe_target }}`

{{ obj.docstring.description if obj.docstring }}

{% if custom_vars.show_source and obj.source %}
## Source
```python
{{ obj.source }}
```
{% endif %}
````