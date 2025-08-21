# Template reference

Complete reference for built-in templates and available context variables.

## Built-in templates

Griffonner ships with these templates for Python documentation:

### `python/default/module.md.jinja2`

Comprehensive module documentation template.

**Features:**
- Module overview and description
- Class listing with method tables  
- Function documentation with signatures
- Attribute documentation with types
- Hierarchical organisation

**Example output:**
```markdown
# mymodule

Module description from docstring.

## Classes

### MyClass

Brief class description.

```python
class MyClass(BaseClass)
```

#### Methods

| Method | Description |
|--------|-------------|
| `__init__` | Initialise the class |
| `process` | Process the data |

## Functions

### my_function

Brief function description.

```python
my_function(param1: str, param2: int = 10) -> bool
```

**Parameters:**

- `param1`: Input string parameter
- `param2`: Optional integer parameter

**Returns:** Success status
```

### `python/default/class.md.jinja2`

Detailed class documentation template.

**Features:**
- Inheritance information
- Class definition with signature
- Attribute table with types
- Detailed method documentation
- Property documentation
- Parameter and return type information

**Example output:**
```markdown
# MyClass

**Inherits from:** BaseClass, MixinClass

Detailed class description from docstring.

## Class Definition

```python
class MyClass(BaseClass, MixinClass):
    """Brief class description."""
    ...
```

## Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `value` | int | The current value |
| `name` | str | Object name |

## Methods

### __init__

Initialise the MyClass instance.

```python
__init__(self, name: str, value: int = 0) -> None
```

**Parameters:**

- `name`: The name for this instance
- `value`: Initial value (default: 0)

### process

Process the stored data.

```python
process(self, data: List[str]) -> Dict[str, Any]
```

**Returns:**

Dictionary containing processed results.

**Raises:**

- `ValueError`: If data is empty or invalid

## Properties

### is_valid

Check if the instance is in a valid state.

```python
@property
def is_valid(self) -> bool:
    ...
```

Returns True if the instance is valid.
```

### `python/default/function.md.jinja2`

Detailed function documentation template.

**Features:**
- Function signature
- Detailed parameter documentation
- Return type and description
- Exception documentation
- Example code blocks

**Example output:**
```markdown
# calculate_total

Calculate the total from a list of values.

## Function Signature

```python
calculate_total(values: List[float], tax_rate: float = 0.1) -> float
```

## Description

This function takes a list of numeric values and calculates their sum,
then applies the specified tax rate to get the final total.

## Parameters

### values

**Type:** List[float]

A list of numeric values to sum. Must not be empty.

### tax_rate

**Type:** float

The tax rate to apply as a decimal (default: 0.1 for 10%).
Must be between 0.0 and 1.0.

## Returns

**Type:** float

The calculated total including tax.

## Raises

### ValueError

Raised when the values list is empty or tax_rate is out of range.

## Examples

```python
# Basic usage
total = calculate_total([10.0, 20.0, 30.0])
print(total)  # 66.0 (60.0 + 10% tax)

# Custom tax rate
total = calculate_total([100.0], tax_rate=0.2)
print(total)  # 120.0
```
```

## Context variables

All templates receive these context variables:

### `obj`

The main Griffe object being documented. Type depends on what's being documented:

**For modules (`griffe.Module`):**
```jinja2
{{ obj.name }}              {# Module name #}
{{ obj.filepath }}          {# Source file path #}
{{ obj.docstring }}         {# Module docstring object #}
{{ obj.members }}           {# Dict of all members #}
{{ obj.classes }}           {# Dict of classes only #}
{{ obj.functions }}         {# Dict of functions only #}
{{ obj.attributes }}        {# Dict of attributes only #}
```

**For classes (`griffe.Class`):**
```jinja2
{{ obj.name }}              {# Class name #}
{{ obj.bases }}             {# List of base classes #}
{{ obj.decorators }}        {# List of decorators #}
{{ obj.methods }}           {# Dict of methods #}
{{ obj.attributes }}        {# Dict of attributes #}
{{ obj.properties }}        {# Dict of properties #}
```

**For functions (`griffe.Function`):**
```jinja2
{{ obj.name }}              {# Function name #}
{{ obj.signature }}         {# Function signature #}
{{ obj.decorators }}        {# List of decorators #}
{{ obj.parameters }}        {# List of parameters #}
{{ obj.returns }}           {# Return annotation #}
```

### `griffe_target`

The target module/object path specified in frontmatter:

```jinja2
{{ griffe_target }}         {# e.g., "mypackage.utils" #}
```

### Custom variables

All variables from frontmatter `custom_vars`:

```yaml
# In frontmatter
custom_vars:
  project_name: "My Project"
  version: "1.0.0"
  emoji: "🚀"
```

```jinja2
{# In template #}
{{ project_name }}          {# "My Project" #}
{{ version }}               {# "1.0.0" #}
{{ emoji }}                 {# "🚀" #}
```

## Docstring objects

Docstring objects provide structured access to documentation:

### Basic properties

```jinja2
{{ obj.docstring.summary }}         {# First line summary #}
{{ obj.docstring.description }}     {# Full description #}
```

### Parameters

```jinja2
{% if obj.docstring.parameters %}
{% for param in obj.docstring.parameters %}
{{ param.name }}                    {# Parameter name #}
{{ param.annotation }}              {# Type annotation #}
{{ param.description }}             {# Parameter description #}
{{ param.default }}                 {# Default value #}
{% endfor %}
{% endif %}
```

### Returns

```jinja2
{% if obj.docstring.returns %}
{{ obj.docstring.returns.annotation }}     {# Return type #}
{{ obj.docstring.returns.description }}    {# Return description #}
{% endif %}
```

### Exceptions

```jinja2
{% if obj.docstring.raises %}
{% for exc in obj.docstring.raises %}
{{ exc.annotation }}                {# Exception type #}
{{ exc.description }}               {# When it's raised #}
{% endfor %}
{% endif %}
```

### Examples

```jinja2
{% if obj.docstring.examples %}
{% for example in obj.docstring.examples %}
{{ example.description }}           {# Example code #}
{{ example.snippet }}               {# Code snippet #}
{% endfor %}
{% endif %}
```

## Member filtering

Filter object members by type and visibility:

### By type

```jinja2
{# Classes only #}
{% for cls in obj.classes.values() %}
{{ cls.name }}
{% endfor %}

{# Functions only #}
{% for func in obj.functions.values() %}
{{ func.name }}
{% endfor %}

{# All members by kind #}
{% for name, member in obj.members.items() %}
{% if member.kind.value == "class" %}
Class: {{ name }}
{% elif member.kind.value == "function" %}
Function: {{ name }}
{% endif %}
{% endfor %}
```

### By visibility

```jinja2
{# Public members only (don't start with _) #}
{% for name, member in obj.members.items() %}
{% if not name.startswith('_') %}
{{ name }}: {{ member.kind.value }}
{% endif %}
{% endfor %}

{# Private members only #}
{% for name, member in obj.members.items() %}
{% if name.startswith('_') and not name.startswith('__') %}
{{ name }}: {{ member.kind.value }}
{% endif %}
{% endfor %}
```

### By decorator

```jinja2
{# Properties only #}
{% for name, member in obj.members.items() %}
{% if member.decorators and 'property' in (member.decorators | map(attribute='value')) %}
Property: {{ name }}
{% endif %}
{% endfor %}

{# Static methods #}
{% for name, member in obj.members.items() %}
{% if member.decorators and 'staticmethod' in (member.decorators | map(attribute='value')) %}
Static method: {{ name }}
{% endif %}
{% endfor %}
```

## Signature handling

Work with function and method signatures:

### Parameters

```jinja2
{% if obj.signature %}
{% for param in obj.signature.parameters %}
{{ param.name }}                    {# Parameter name #}
{{ param.annotation }}              {# Type annotation #}
{{ param.default }}                 {# Default value #}
{{ param.kind.value }}              {# "positional", "keyword", etc. #}
{% endfor %}
{% endif %}
```

### Return type

```jinja2
{% if obj.signature and obj.signature.returns %}
{{ obj.signature.returns }}         {# Return type annotation #}
{% endif %}
```

### Full signature

```jinja2
{{ obj.signature }}                 {# Complete function signature #}
```

## Useful filters

Jinja2 filters for common formatting tasks:

### String manipulation

```jinja2
{{ obj.name | title }}              {# Title case #}
{{ obj.name | upper }}              {# UPPER CASE #}
{{ obj.name | lower }}              {# lower case #}
{{ obj.name | replace('_', ' ') }}  {# Replace underscores #}
```

### Lists and joining

```jinja2
{{ obj.bases | join(', ') }}        {# Join with commas #}
{{ obj.parameters | map(attribute='name') | join(', ') }}  {# Map then join #}
{{ obj.members.keys() | list }}     {# Convert to list #}
```

### Defaults and fallbacks

```jinja2
{{ obj.docstring.summary | default("No description") }}
{{ custom_var | default("Default value") }}
{{ obj.annotation | default("Any") }}
```

### Length and counting

```jinja2
{{ obj.classes | length }}          {# Number of classes #}
{{ obj.name | length }}             {# String length #}

{% if obj.methods | length > 0 %}
Has methods
{% endif %}
```

## Template inheritance

Use Jinja2 template inheritance for consistency:

**Base template (`base.md.jinja2`):**
```jinja2
# {{ title | default(obj.name) }}

{% block summary %}
{{ obj.docstring.summary if obj.docstring else "No description" }}
{% endblock %}

{% block content %}
{# Override in child templates #}
{% endblock %}

---
*Generated with Griffonner from {{ griffe_target }}*
```

**Child template:**
```jinja2
{% extends "base.md.jinja2" %}

{% block content %}
## Classes
{% for class_obj in obj.classes.values() %}
### {{ class_obj.name }}
{{ class_obj.docstring.summary if class_obj.docstring }}
{% endfor %}
{% endblock %}
```

## Conditional rendering

Handle missing or optional information:

```jinja2
{# Safe docstring access #}
{% if obj.docstring %}
{{ obj.docstring.description }}
{% else %}
*No documentation available.*
{% endif %}

{# Check for empty collections #}
{% if obj.classes %}
## Classes
{% for cls in obj.classes.values() %}
{{ cls.name }}
{% endfor %}
{% else %}
*No classes defined.*
{% endif %}

{# Multiple conditions #}
{% if obj.docstring and obj.docstring.parameters %}
## Parameters
{% for param in obj.docstring.parameters %}
- {{ param.name }}: {{ param.description }}
{% endfor %}
{% endif %}
```

## Next steps

- Learn about [template development](templates.md)
- Check the [CLI reference](cli-reference.md) for validation
- See [watch mode](watch-mode.md) for template development workflow