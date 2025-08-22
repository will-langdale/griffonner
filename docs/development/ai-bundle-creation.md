# AI bundle creation

Copy this comprehensive prompt into any LLM to get help creating complete Griffonner plugin bundles:

````text
I want to create a Griffonner plugin bundle. Griffonner is a Python documentation generator with an extensible plugin system.

## What I need help with:

Create a complete plugin bundle that includes processors, filters, and templates for [DESCRIBE YOUR USE CASE HERE - e.g., "generating documentation for FastAPI applications", "creating Sphinx-style documentation", "generating GitLab wiki pages"].

## Bundle architecture:

A Griffonner bundle combines:
- **Processors**: Transform Griffe objects before template rendering (add metadata, analyse code, etc.)
- **Filters**: Custom Jinja2 template filters for data formatting
- **Templates**: Jinja2 templates optimised for specific output formats
- **Entry points**: Python packaging configuration for automatic discovery

## Bundle class structure:

```python
from griffonner.plugins import BaseBundle
from typing import Dict, List, Any

class MyBundle(BaseBundle):
    @property
    def name(self) -> str:
        return "my-bundle"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Description of what this bundle does"
    
    def get_processors(self) -> Dict[str, Any]:
        """Return processors provided by this bundle."""
        return {
            "processor_name": ProcessorClass(),
        }
    
    def get_filters(self) -> Dict[str, Any]:
        """Return filters provided by this bundle."""
        return {
            "filter_name": filter_function,
        }
    
    def get_template_paths(self) -> List[str]:
        """Return template directory paths."""
        return ["templates/my-bundle/"]
```

## Processor example:

```python
from griffonner.plugins import BaseProcessor
from typing import Any, Dict, Tuple, Union
from griffe import Object as GriffeObject, Alias

class MyProcessor(BaseProcessor):
    @property
    def name(self) -> str:
        return "my_processor"
    
    @property
    def priority(self) -> int:
        return 100  # Default priority
    
    def process(
        self, 
        griffe_obj: Union[GriffeObject, Alias], 
        context: Dict[str, Any]
    ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        """Transform griffe_obj and add data to context."""
        
        # Get configuration from frontmatter
        config = context.get("processor_config", {})
        
        # Analyse the object and add data to context
        analysis_result = self.analyse_object(griffe_obj, config)
        context["my_data"] = analysis_result
        
        return griffe_obj, context
    
    def analyse_object(self, obj, config):
        """Your custom analysis logic here."""
        return {"analysed": True, "name": obj.name}
```

## Filter examples:

```python
def format_for_my_platform(text):
    """Format text for specific platform/output."""
    if not text:
        return text
    # Your formatting logic here
    return formatted_text

def create_badge(value, type="info"):
    """Create visual badges for documentation."""
    badges = {
        "info": f"ℹ️ {value}",
        "warning": f"⚠️ {value}", 
        "error": f"❌ {value}",
        "success": f"✅ {value}"
    }
    return badges.get(type, f"📝 {value}")
```

## Template example:

```jinja2
{# templates/my-bundle/module.md.jinja2 #}
# {{ obj.name }}

{{ obj.docstring.summary if obj.docstring }}

{% if my_data %}
**Analysis**: {{ my_data.analysed | create_badge("success") }}
{% endif %}

## Functions

{% for name, func in obj.members.items() if func.kind.value == "function" %}
### {{ func.name }}

{{ func.docstring.summary if func.docstring }}

{% if func.signature %}
**Signature**: {{ func.signature | format_for_my_platform }}
{% endif %}
{% endfor %}
```

## Entry points configuration (pyproject.toml):

```toml
[project.entry-points."griffonner.bundles"]
my-bundle = "my_package:MyBundle"

# Optional: Direct access to components
[project.entry-points."griffonner.processors"]
my_processor = "my_package.processors:MyProcessor"

[project.entry-points."griffonner.filters"]
format_for_my_platform = "my_package.filters:format_for_my_platform"
create_badge = "my_package.filters:create_badge"
```

## Package structure:

```
my-griffonner-bundle/
├── my_bundle/
│   ├── __init__.py          # Export MyBundle
│   ├── bundle.py            # Bundle class
│   ├── processors.py        # Processor classes
│   └── filters.py           # Filter functions
├── templates/
│   └── my-bundle/
│       ├── module.md.jinja2
│       └── class.md.jinja2
├── tests/
│   └── test_bundle.py
├── pyproject.toml
└── README.md
```

## Testing:

```python
def test_my_bundle():
    bundle = MyBundle()
    
    assert bundle.name == "my-bundle"
    assert "my_processor" in bundle.get_processors()
    assert "format_for_my_platform" in bundle.get_filters()

def test_processor():
    processor = MyProcessor()
    
    # Mock Griffe object
    from unittest.mock import Mock
    mock_obj = Mock()
    mock_obj.name = "test_module"
    
    context = {}
    result_obj, result_context = processor.process(mock_obj, context)
    
    assert "my_data" in result_context
```

## Usage example:

Users install and use the bundle like this:

```shell
pip install my-griffonner-bundle
griffonner bundle my-bundle  # Show bundle info
```

```yaml
# docs/pages/api.md
---
template: "my-bundle/module.md.jinja2"
griffe_target: "myproject.api"
processors:
  enabled: ["my-bundle.my_processor"]
  config:
    custom_setting: "value"
output:
  - filename: "API.md"
    griffe_target: "myproject.api"
---
```

## Griffe object structure:

The griffe_obj parameter contains parsed Python code with these common properties:

- `obj.name` - Object name
- `obj.kind.value` - "module", "class", "function", etc.
- `obj.docstring.summary` - First line of docstring
- `obj.docstring.description` - Full docstring text  
- `obj.members` - Dict of child objects (functions, classes, etc.)
- `obj.signature` - Function signature (for functions)
- `obj.signature.parameters` - List of parameters
- `obj.signature.returns` - Return type annotation
- `obj.decorators` - List of decorators
- `obj.labels` - Set of labels ("property", "classmethod", etc.)

## Please help me create:

1. **Bundle purpose**: [Describe what documentation format/platform you're targeting]
2. **Processors needed**: [What analysis/transformation do you need?]  
3. **Filters needed**: [What formatting/conversion do you need?]
4. **Templates**: [What should the output look like?]
5. **Special requirements**: [Any specific features or constraints?]

Generate the complete bundle code with proper Python packaging, entry points, and example usage.
````