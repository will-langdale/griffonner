# AI template guide

Copy and paste this into any LLM to get help creating Griffonner templates:

````text
I'm using Griffonner, a Python documentation generator. Help me create Jinja2 templates for documenting my Python code.

## How Griffonner works:

1. Griffonner uses Griffe to parse Python modules and Jinja2 templates to generate documentation
2. I create markdown files with YAML frontmatter that specify:
   - template: path to Jinja2 template (e.g., "python/simple/module.md.jinja2")  
   - output: list with filename and griffe_target (Python module name)
   - custom_vars: any custom variables for the template

3. Templates get access to:
   - obj: the raw Griffe object with all module/class/function data
   - custom_vars: any variables I defined in frontmatter
   - source_content: the markdown content after frontmatter
   - source_path: path to the source file

## Common Griffe object properties:

- obj.name: module/class/function name
- obj.kind.value: "module", "class", "function", etc.
- obj.docstring.summary: first line of docstring  
- obj.docstring.description: full docstring text
- obj.members: dictionary of child objects (functions, classes, etc.)
- obj.signature: function signature info (for functions)
- obj.signature.parameters: list of parameters with name, annotation, default
- obj.signature.returns: return type annotation
- obj.decorators: list of decorators applied to the object
- obj.labels: set of labels (e.g., "property", "classmethod", "staticmethod")

## Template examples:

### Basic module template:
```jinja2
# {{ obj.name }} module

{{ obj.docstring.summary if obj.docstring else "No description available" }}

## Functions
{% for name, func in obj.members.items() if func.kind.value == "function" %}
### `{{ func.name }}`
{{ func.docstring.summary if func.docstring }}
{% endfor %}
```

### Function signature template:
```jinja2
```python
{{ func.name }}({% for param in func.signature.parameters %}{{ param.name }}{% if param.annotation %}: {{ param.annotation }}{% endif %}{% if param.default %} = {{ param.default }}{% endif %}{% if not loop.last %}, {% endif %}{% endfor %}){% if func.signature.returns %} -> {{ func.signature.returns }}{% endif %}
```
```

### Class template:
```jinja2
## {{ obj.name }}
{{ obj.docstring.summary if obj.docstring }}

### Methods
{% for name, method in obj.members.items() if method.kind.value == "function" %}
#### `{{ method.name }}`
{{ method.docstring.summary if method.docstring }}
{% endfor %}
```

## CLI usage:
- griffonner generate docs/pages/ --output docs/output
- griffonner templates --template-dir docs/templates

Please help me create templates for my specific documentation needs.
````