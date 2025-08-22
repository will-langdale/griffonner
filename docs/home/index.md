# Griffonner

Template-first Python documentation generator that gets out of your way.

> *From French "griffonner" (to scribble/draft) - because [Griffe](https://mkdocstrings.github.io/griffe/) finds it, you sketch it out*

## Overview

Griffonner uses [Griffe](https://mkdocstrings.github.io/griffe/) to parse Python code and Jinja2 templates to generate documentation in any format. It has zero opinions about output structure - you control everything through templates.

**Core flow**: Python Code � Griffe Parser � Template Engine � Your Output

## Basic example

Let's document Python's built-in `json` module to show how Griffonner works.

### Step 1: Create a template

First, create a simple template at `docs/templates/python/simple/module.md.jinja2`:

```jinja2
# {{ obj.name }} module

{{ obj.docstring.summary if obj.docstring else "No description available" }}

{% if obj.docstring and obj.docstring.description %}
{{ obj.docstring.description }}
{% endif %}

## Functions

{% for name, func in obj.members.items() %}
{% if func.kind.value == "function" and not name.startswith('_') %}
### `{{ func.name }}({{ func.signature.parameters | map(attribute='name') | join(', ') if func.signature }})`

{{ func.docstring.summary if func.docstring else "No description" }}

{% if func.signature and func.signature.parameters %}
**Parameters:**

{% for param in func.signature.parameters %}
- `{{ param.name }}`: {{ param.annotation if param.annotation else "Any" }}
{% endfor %}
{% endif %}

{% if func.signature and func.signature.returns %}
**Returns:** {{ func.signature.returns }}
{% endif %}

---
{% endif %}
{% endfor %}

## Classes  

{% for name, cls in obj.members.items() %}
{% if cls.kind.value == "class" and not name.startswith('_') %}
### {{ cls.name }}

{{ cls.docstring.summary if cls.docstring else "No description" }}

{% endif %}
{% endfor %}

---
*Generated with Griffonner from {{ griffe_target }}*
```

### Step 2: Create a page with frontmatter

Create `docs/pages/json-module.md`:

```markdown
---
template: "python/simple/module.md.jinja2"
output:
  - filename: "json-module.md"
    griffe_target: "json"
custom_vars:
  title: "JSON module documentation"
---

This page documents Python's built-in JSON module.
```

### Step 3: Generate documentation

```shell
# Install griffonner
pip install griffonner

# Generate the documentation
griffonner generate docs/pages/json-module.md --output docs/output
```

### Step 4: Result

This generates `docs/output/pages/json-module.md` with content like:

```markdown
# json module

JSON (JavaScript Object Notation) encoder and decoder.

## Functions

### `loads(s, *, cls, object_hook, parse_float, parse_int, parse_constant, object_pairs_hook, **kw)`

Deserialise a JSON document from a string.

**Parameters:**

- `s`: str
- `cls`: Optional[Type[JSONDecoder]]
- `object_hook`: Optional[Callable[[Dict[Any, Any]], Any]]
- `parse_float`: Optional[Callable[[str], Any]]

**Returns:** Any

---

### `dumps(obj, *, skipkeys, ensure_ascii, check_circular, allow_nan, cls, indent, separators, default, sort_keys, **kw)`

Serialise obj to a JSON formatted str.

**Parameters:**

- `obj`: Any
- `skipkeys`: bool
- `ensure_ascii`: bool

**Returns:** str

---

## Classes

### JSONDecoder

Simple JSON decoder.

### JSONEncoder  

Extensible JSON encoder for Python data structures.

---
*Generated with Griffonner from json*
```

## Key features

- **Zero opinions**: Templates control all formatting and structure
- **Frontmatter-driven**: Configuration lives in your markdown files  
- **Format agnostic**: Generate Markdown, RST, HTML, JSON - anything
- **Template ecosystem**: Share and reuse templates across projects
- **Griffe-powered**: Rich Python code analysis and parsing

## CLI commands

```shell
# Generate all files in a directory
griffonner generate docs/pages/ --output docs/output

# Generate a single file
griffonner generate docs/pages/api.md --output docs/output

# List available templates
griffonner templates

# Validate template syntax
griffonner validate python/default/module.md.jinja2

# Watch mode - live reload during development
griffonner watch docs/pages/ --output docs/output
```

### Watch mode

Watch mode provides live reload functionality for development workflows:

```shell
# Start watching a directory
griffonner watch docs/pages/

# Watch with custom output directory  
griffonner watch docs/pages/ --output docs/generated

# Watch with additional template directories
griffonner watch docs/pages/ --template-dir custom-templates/
```

When files with frontmatter are modified, Griffonner automatically regenerates the corresponding output files.

### Template discovery

Griffonner automatically searches for templates in these locations:

1. `docs/templates/` (project templates)
2. `templates/` (current directory)  
3. Built-in templates (shipped with Griffonner)

```shell
# List all available templates
griffonner templates

# Search for specific patterns
griffonner templates --pattern "**/*class*"

# Include custom template directories
griffonner templates --template-dir custom-templates/
```

