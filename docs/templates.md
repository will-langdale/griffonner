# Template development

Learn how to create and customise templates for Griffonner.

## Template basics

Griffonner templates use Jinja2 syntax with rich context from Griffe's Python code analysis.

### Template structure

Templates are Jinja2 files that generate documentation from Python code analysis:

```jinja2
# {{ obj.name }}

{% if obj.docstring -%}
{{ obj.docstring.description }}
{% endif %}

## Classes
{% for class_obj in obj.classes.values() %}
### {{ class_obj.name }}
{{ class_obj.docstring.summary if class_obj.docstring else "No description" }}
{% endfor %}
```

### Template context

Every template receives this context:

- `obj` - The Griffe object (module, class, function) being documented
- `griffe_target` - The target module/object path
- Custom variables from frontmatter `custom_vars`

## Template discovery

Griffonner searches for templates in this order:

1. Custom directories (specified with `--template-dir`)
2. `docs/templates/` in your project
3. `templates/` in current directory  
4. Built-in templates

### Template organisation

Organise templates by language and style:

```
templates/
├── python/
│   ├── default/
│   │   ├── module.md.jinja2
│   │   ├── class.md.jinja2
│   │   └── function.md.jinja2
│   ├── sphinx-style/
│   │   └── module.md.jinja2
│   └── gitlab-wiki/
│       └── module.md.jinja2
└── rust/
    └── default/
        └── module.md.jinja2
```

## Creating templates

### 1. Understanding the Griffe object

The `obj` context variable is a Griffe object with rich metadata:

```jinja2
{# Module information #}
{{ obj.name }}                    {# Module name #}
{{ obj.filepath }}                {# Source file path #}
{{ obj.docstring.description }}   {# Module docstring #}

{# Members #}
{% for name, member in obj.members.items() %}
  {{ member.kind.value }}         {# "class", "function", "attribute" #}
  {{ member.name }}
{% endfor %}
```

### 2. Working with classes

```jinja2
{% for class_obj in obj.classes.values() %}
# {{ class_obj.name }}

{# Inheritance #}
{% if class_obj.bases %}
Inherits from: {{ class_obj.bases | join(', ') }}
{% endif %}

{# Methods #}
{% for method in class_obj.methods.values() %}
## {{ method.name }}
{{ method.docstring.summary if method.docstring }}

```python
{{ method.signature }}
```
{% endfor %}
{% endfor %}
```

### 3. Working with functions

```jinja2
{% for func in obj.functions.values() %}
# {{ func.name }}

{{ func.docstring.summary if func.docstring }}

## Signature
```python  
{{ func.signature }}
```

{% if func.docstring and func.docstring.parameters %}
## Parameters
{% for param in func.docstring.parameters %}
- **{{ param.name }}**: {{ param.description }}
{% endfor %}
{% endif %}

{% if func.docstring and func.docstring.returns %}
## Returns
{{ func.docstring.returns.description }}
{% endif %}
{% endfor %}
```

### 4. Using custom variables

Access custom variables from frontmatter:

```jinja2
{# From frontmatter custom_vars #}
{{ emoji | default("📚") }} {{ title | default(obj.name) }}

Version: {{ version | default("Unknown") }}
Category: {{ category | default("General") }}
```

Corresponding frontmatter:

```yaml
---
template: "python/custom/module.md.jinja2"
custom_vars:
  emoji: "🔧"
  title: "Utilities module"
  version: "2.1.0"
  category: "Core"
---
```

## Advanced techniques

### Conditional sections

Show sections only when content exists:

```jinja2
{% if obj.classes %}
## Classes
{% for class_obj in obj.classes.values() %}
### {{ class_obj.name }}
{{ class_obj.docstring.summary if class_obj.docstring }}
{% endfor %}
{% endif %}

{% if obj.functions %}
## Functions
{# ... #}
{% endif %}
```

### Filtering members

Hide private members and filter by type:

```jinja2
{# Public functions only #}
{% for func in obj.functions.values() %}
{% if not func.name.startswith('_') %}
### {{ func.name }}
{{ func.docstring.summary if func.docstring }}
{% endif %}
{% endfor %}

{# Filter by decorator #}
{% for func in obj.functions.values() %}
{% if func.decorators and 'property' in func.decorators | map(attribute='value') %}
### {{ func.name }} (property)
{% endif %}
{% endfor %}
```

### Cross-references

Create links between documentation:

```jinja2
{# Link to other modules #}
See also: [{{ related_module }}]({{ related_module }}.md)

{# Generate table of contents #}
## Contents
{% for class_obj in obj.classes.values() %}
- [{{ class_obj.name }}](#{{ class_obj.name | lower }})
{% endfor %}
```

### Multiple output formats

Templates can generate any text format:

**Markdown template:**
```jinja2
# {{ obj.name }}

## Overview
{{ obj.docstring.description if obj.docstring }}
```

**reStructuredText template:**
```jinja2
{{ obj.name }}
{{ "=" * obj.name | length }}

Overview
--------
{{ obj.docstring.description if obj.docstring }}
```

**JSON template:**
```jinja2
{
  "module": "{{ obj.name }}",
  "description": "{{ obj.docstring.summary if obj.docstring }}",
  "classes": [
    {% for class_obj in obj.classes.values() -%}
    {
      "name": "{{ class_obj.name }}",
      "methods": {{ class_obj.methods.keys() | list | tojson }}
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  ]
}
```

## Template validation

Validate your templates before using them:

```shell
# Check syntax
griffonner validate python/custom/module.md.jinja2

# Test with actual data
griffonner generate test-file.md --output test-output/
```

## Built-in template reference

Griffonner ships with these built-in templates:

### `python/default/module.md.jinja2`

- Comprehensive module documentation
- Classes with method tables
- Functions with signatures and parameters
- Attributes with type information

### `python/default/class.md.jinja2`

- Detailed class documentation
- Inheritance information
- Method documentation with examples
- Property and attribute listing

### `python/default/function.md.jinja2`

- Function signature and parameters
- Return type documentation
- Docstring parsing with sections
- Example usage if available

## Best practices

### 1. Template organisation

- Use consistent naming: `<language>/<style>/<type>.md.jinja2`
- Group related templates in directories
- Include README files explaining template sets

### 2. Content structure

- Start with object name and summary
- Group related information in sections
- Use consistent heading levels
- Include metadata (source file, generation time)

### 3. Error handling

Handle missing information gracefully:

```jinja2
{# Safe docstring access #}
{{ obj.docstring.summary if obj.docstring else "No description available" }}

{# Check for empty collections #}
{% if obj.functions %}
## Functions
{% for func in obj.functions.values() %}
{# ... #}
{% endfor %}
{% else %}
*No public functions.*
{% endif %}
```

### 4. Performance

- Avoid complex logic in templates
- Use filters efficiently
- Cache expensive operations in custom variables

### 5. Maintainability

- Comment complex template logic
- Use descriptive variable names
- Keep templates focused on single purposes

## Sharing templates

### Template packages

Create reusable template packages:

```
my-templates/
├── README.md
├── python/
│   └── sphinx-style/
│       ├── module.md.jinja2
│       ├── class.md.jinja2
│       └── function.md.jinja2
└── examples/
    └── usage.md
```

### Usage

```shell
# Use shared templates
griffonner generate docs/pages/ --template-dir ~/shared-templates/
```

### Distribution

- Share via Git repositories
- Package as Python distributions
- Include example frontmatter
- Document template variables and context

## Troubleshooting

### Common errors

**Template not found:**
- Check template path spelling
- Verify template directory exists
- Use `griffonner templates` to list available templates

**Syntax errors:**
```
❌ Template syntax error in custom/broken.md.jinja2: unexpected '}'
```
- Check Jinja2 syntax
- Balance `{% %}` and `{{ }}` tags
- Use `griffonner validate` to check syntax

**Missing variables:**
- Check frontmatter `custom_vars` section
- Use default filters: `{{ variable | default("fallback") }}`
- Test with minimal frontmatter first

### Debugging templates

Add debug output to templates:

```jinja2
{# Debug: Show available variables #}
<!-- 
Object type: {{ obj.__class__.__name__ }}
Object name: {{ obj.name }}
Available attrs: {{ obj.__dict__.keys() | list }}
-->

{# Continue with template... #}
```

## Next steps

- Explore the [template reference](template-reference.md)
- Learn about [watch mode](watch-mode.md) for development
- Check the [CLI reference](cli-reference.md) for validation commands