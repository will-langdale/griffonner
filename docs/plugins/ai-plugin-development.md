# AI plugin development

Copy this prompt into any LLM to get help creating simple Griffonner plugins:

```
I want to create a Griffonner plugin. Griffonner is a Python documentation generator with a plugin system that supports processors and filters.

## Plugin types:

**Processors**: Transform Griffe objects before template rendering
- Input: Griffe object + template context
- Output: Modified Griffe object + updated context  
- Used for: Adding metadata, computing values, enriching data

**Filters**: Custom Jinja2 template filters for data transformation
- Input: Any value + optional arguments
- Output: Transformed value
- Used for: Formatting, converting, styling data in templates

## Creating a simple processor:

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
        # Add custom data to context
        context["my_data"] = self.analyse_object(griffe_obj)
        return griffe_obj, context
    
    def analyse_object(self, obj):
        # Your custom logic here
        return {"processed": True}
```

## Creating a simple filter:

```python
def my_filter(value, arg1="default"):
    """Custom Jinja2 filter function"""
    return f"processed: {value} with {arg1}"

# Use in templates: {{ obj.name | my_filter("custom") }}
```

## Entry points configuration (pyproject.toml):

```toml
[project.entry-points."griffonner.processors"]
my_processor = "mypackage:MyProcessor"

[project.entry-points."griffonner.filters"] 
my_filter = "mypackage:my_filter"
```

## Using plugins:

**In frontmatter**:
```yaml
processors:
  enabled: ["my_processor"]
  config:
    custom_setting: "value"
```

**In templates**:
```jinja2
{{ obj.name | my_filter("argument") }}

{% if my_data %}
Custom data: {{ my_data.processed }}
{% endif %}
```

## Testing:

```python
def test_my_processor():
    processor = MyProcessor()
    mock_obj = Mock()  # Mock Griffe object
    context = {}
    
    result_obj, result_context = processor.process(mock_obj, context)
    
    assert "my_data" in result_context
    assert result_context["my_data"]["processed"] is True
```

Please help me create a specific processor or filter for my documentation needs. Tell me what you want the plugin to do and I'll help you implement it.
```