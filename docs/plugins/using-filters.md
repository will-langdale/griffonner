# Using filters

Custom Jinja2 filters extend your templates with data transformation capabilities. Filters are functions that take an input value, transform it, and return the result, used with the pipe syntax in templates.

## What filters do

Filters transform data in templates:

- Format strings, numbers, and dates
- Convert data types (lists to strings, objects to JSON)
- Apply formatting rules (code syntax, links, emphasis)
- Perform calculations or data processing

## Basic usage

Filters are automatically loaded from installed plugins and used in templates:

```jinja2
{# Format a function signature #}
{{ func.signature | format_signature }}

{# Convert complexity score to badge #}
{{ complexity_score | complexity_badge }}

{# Format docstring for GitLab wiki #}
{{ func.docstring.description | gitlab_links }}
```

## Installing filters

Filters come from Python packages with entry points:

```shell
# Example packages (aspirational - not yet available)
pip install griffonner-formatters
pip install griffonner-gitlab-wiki
```

After installation, filters are automatically discovered and available in all templates.

## Available filters

List all available filters:

```shell
griffonner plugins
```

This shows filters along with processors and bundles from installed plugins.

## Built-in filters

In addition to custom filters, all standard Jinja2 filters are available:

```jinja2
{# Standard Jinja2 filters #}
{{ obj.name | upper }}
{{ func.docstring.summary | truncate(50) }}
{{ obj.members | length }}

{# Custom plugin filters #}
{{ func.signature | format_signature }}
{{ docstring | markdown_to_html }}
```

## Common filter patterns

### String formatting

```jinja2
{# Format function signatures #}
{{ func.signature | format_signature }}
# Result: function_name(
#     param1: str,
#     param2: int = 42
# ) -> bool

{# Format module paths #}
{{ obj.path | format_module_path }}
# Result: mypackage.utils → mypackage → utils
```

### Link generation

```jinja2
{# Generate documentation links #}
{{ func.name | doc_link(base_url="https://docs.example.com") }}
# Result: [function_name](https://docs.example.com/api/function_name)

{# GitLab wiki links #}
{{ obj.name | gitlab_wiki_link }}
# Result: [[API Reference | function_name]]
```

### Data transformation

```jinja2
{# Convert objects to JSON #}
{{ func.parameters | to_json }}
# Result: {"param1": "str", "param2": "int"}

{# Format lists #}
{{ obj.decorators | format_decorator_list }}
# Result: @property, @staticmethod
```

### Conditional formatting

```jinja2
{# Add badges based on data #}
{{ complexity_score | complexity_badge }}
# Result: 🟢 Simple (score: 3)
# Result: 🔴 Complex (score: 15)

{# Format types with icons #}
{{ obj.kind | type_icon }} {{ obj.name }}
# Result: 📦 MyClass
# Result: ⚙️ my_function
```

## Filter arguments

Filters can accept arguments:

```jinja2
{# Positional arguments #}
{{ docstring | truncate(100, "...") }}

{# Keyword arguments #}
{{ func.name | doc_link(base_url="https://docs.example.com", format="markdown") }}

{# Mixed arguments #}
{{ complexity_score | format_badge("warning", threshold=10) }}
```

## Chain multiple filters

Combine filters for complex transformations:

```jinja2
{# Chain filters together #}
{{ func.docstring.summary | markdown_to_html | truncate(200) | safe }}

{# Complex formatting chain #}
{{ obj.parameters | extract_types | format_type_list | wrap_code_blocks }}
```

## Filter conflicts

If multiple plugins provide filters with the same name, the last loaded plugin wins. Check for conflicts:

```shell
griffonner plugins
```

Look for duplicate filter names in the output. To avoid conflicts:

- Use namespaced filter names: `gitlab_wiki_link` instead of `link`
- Check existing filters before installing new plugins
- Remove unused plugin packages

## Examples

### GitLab wiki formatting

```jinja2
# {{ obj.name | title_case }} 

{{ obj.docstring.summary | gitlab_emphasis }}

## Functions

{% for name, func in obj.functions.items() %}
### {{ func.name | code_format }}

{{ func.docstring.description | gitlab_links | safe }}

{% if func.signature %}
**Signature**: {{ func.signature | format_signature | code_block }}
{% endif %}
{% endfor %}
```

### API documentation badges

```jinja2
# {{ obj.name }} {{ obj.kind | type_badge }}

{% for name, member in obj.members.items() %}
## {{ member.name }} {{ member.kind | type_badge }}

{% if member.complexity %}
{{ member.complexity | complexity_badge }}
{% endif %}

{{ member.docstring.summary }}
{% endfor %}
```

### Code formatting

```jinja2
{% for func in obj.functions %}
### `{{ func.name }}` {{ func.visibility | visibility_badge }}

```python
{{ func.signature | format_signature }}
```

{{ func.docstring.description | highlight_code("python") | safe }}
{% endfor %}
```

## Troubleshooting

### Filter not found

```
jinja2.exceptions.UndefinedError: 'format_signature' is undefined
```

- Check the filter is installed: `griffonner plugins`
- Verify plugin package is installed: `pip list | grep griffonner`
- Check filter name spelling in template

### Filter error

```
❌ Template rendering failed: Filter 'complexity_badge' error: Expected number, got string
```

- Check filter documentation for expected input types
- Verify the data being passed to filter is correct type
- Debug with `{{ variable | pprint }}` to inspect data

### Missing arguments

```
❌ Filter 'doc_link' missing required argument 'base_url'
```

- Add required arguments: `{{ name | doc_link(base_url="...") }}`
- Check filter documentation for required parameters

## See also

- [Managing plugins](managing-plugins.md) - Installing and discovering plugins
- [Using processors](using-processors.md) - Transform Griffe objects before templating
- [Template development](../template-guides/template-development.md) - Creating templates with filters
- [Plugin development](../development/plugin-development.md) - Creating custom filters