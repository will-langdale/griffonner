# Plugin development

Create custom processors and filters to extend Griffonner's functionality. This guide covers everything from basic plugin creation to publishing on PyPI.

## Plugin architecture

Griffonner plugins use Python's entry points system for automatic discovery. Plugins provide:

- **Processors**: Transform Griffe objects before template rendering
- **Filters**: Add custom Jinja2 template filters

## Creating processors

### Basic processor

Processors implement the `ProcessorProtocol` or inherit from `BaseProcessor`:

```python
from griffonner.plugins import BaseProcessor
from typing import Any, Dict, Tuple, Union
from griffe import Object as GriffeObject, Alias

class ComplexityProcessor(BaseProcessor):
    @property
    def name(self) -> str:
        return "complexity_analyser"
    
    @property  
    def priority(self) -> int:
        return 100  # Default priority
    
    def process(
        self, 
        griffe_obj: Union[GriffeObject, Alias], 
        context: Dict[str, Any]
    ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        """Analyse code complexity and add to context."""
        complexity_data = self.calculate_complexity(griffe_obj)
        context["complexity"] = complexity_data
        return griffe_obj, context
    
    def calculate_complexity(self, obj: Union[GriffeObject, Alias]) -> Dict[str, Any]:
        """Calculate complexity metrics for the object."""
        if obj.kind.value != "function":
            return {}
        
        # Basic cyclomatic complexity calculation
        # In reality, you'd use ast parsing or similar
        score = 1  # Base complexity
        
        # Add complexity for control structures, etc.
        source = getattr(obj, 'source', '')
        score += source.count('if ')
        score += source.count('for ')
        score += source.count('while ')
        score += source.count('except ')
        
        return {
            "score": score,
            "level": "simple" if score < 5 else "complex" if score < 10 else "very_complex"
        }
```

### Using processor configuration

Access user configuration from frontmatter:

```python
def process(self, griffe_obj, context):
    # Get configuration from frontmatter
    config = context.get("processor_config", {})
    threshold = config.get("complexity_threshold", 10)
    
    complexity = self.calculate_complexity(griffe_obj)
    
    # Use threshold in analysis
    if complexity["score"] > threshold:
        context["warnings"] = context.get("warnings", [])
        context["warnings"].append(f"High complexity: {griffe_obj.name}")
    
    context["complexity"] = complexity
    return griffe_obj, context
```

### Simple processors

For basic transformations, use `SimpleProcessor`:

```python
from griffonner.plugins import SimpleProcessor

def add_metadata(griffe_obj, context):
    """Add custom metadata to context."""
    context["build_time"] = datetime.now().isoformat()
    context["generator"] = "my-plugin v1.0"
    return griffe_obj, context

# Create processor instance
metadata_processor = SimpleProcessor(
    name="metadata_adder",
    process_func=add_metadata,
    priority=50  # Run early
)
```

### Processor priorities

Control execution order with priority:

- **50 and below**: Early processing (pre-analysis)
- **100** (default): Standard processing
- **150 and above**: Late processing (post-analysis)

```python
class EarlyProcessor(BaseProcessor):
    @property
    def priority(self) -> int:
        return 50  # Runs before default processors

class LateProcessor(BaseProcessor):
    @property 
    def priority(self) -> int:
        return 150  # Runs after default processors
```

## Creating filters

### Basic filters

Filters are regular Python functions:

```python
def format_signature(signature_obj):
    """Format function signature with proper indentation."""
    if not signature_obj or not hasattr(signature_obj, 'parameters'):
        return str(signature_obj)
    
    params = []
    for param in signature_obj.parameters:
        param_str = param.name
        
        if param.annotation:
            param_str += f": {param.annotation}"
        
        if param.default:
            param_str += f" = {param.default}"
            
        params.append(param_str)
    
    if len(params) <= 2:
        return f"({', '.join(params)})"
    
    # Multi-line format for many parameters
    return f"(\n    {',\n    '.join(params)}\n)"

def complexity_badge(complexity_data):
    """Convert complexity data to a visual badge."""
    if isinstance(complexity_data, dict):
        score = complexity_data.get("score", 0)
    else:
        score = int(complexity_data)
    
    if score < 5:
        return f"🟢 Simple (score: {score})"
    elif score < 10:
        return f"🟡 Moderate (score: {score})"
    else:
        return f"🔴 Complex (score: {score})"

def to_json(obj, indent=2):
    """Convert object to JSON string."""
    import json
    return json.dumps(obj, indent=indent, default=str)
```

### Filters with arguments

Filters can accept positional and keyword arguments:

```python
def doc_link(name, base_url="", format="markdown", prefix=""):
    """Generate documentation links."""
    url = f"{base_url.rstrip('/')}/{prefix}{name}".replace('//', '/')
    
    if format == "markdown":
        return f"[{name}]({url})"
    elif format == "html":
        return f'<a href="{url}">{name}</a>'
    elif format == "rst":
        return f"`{name} <{url}>`_"
    else:
        return url

# Usage in templates:
# {{ func.name | doc_link(base_url="https://docs.example.com", format="markdown") }}
```

### Advanced filters

For complex logic, create filter classes:

```python
class GitLabFormatter:
    """GitLab wiki formatting filter."""
    
    def __init__(self, base_url=""):
        self.base_url = base_url
    
    def __call__(self, text):
        """Format text for GitLab wiki."""
        # Convert markdown links to GitLab wiki links
        text = self.convert_links(text)
        # Add GitLab-specific formatting
        text = self.add_emphasis(text)
        return text
    
    def convert_links(self, text):
        import re
        # Convert [text](url) to [[url | text]]
        pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
        return re.sub(pattern, r'[[\2 | \1]]', text)
    
    def add_emphasis(self, text):
        # Add GitLab-specific emphasis
        return text.replace("**", "'''").replace("*", "''")

# Create filter instance
gitlab_formatter = GitLabFormatter(base_url="https://gitlab.example.com")
```

## Entry points configuration

### Using pyproject.toml

Configure entry points to make plugins discoverable:

```toml
[project]
name = "griffonner-complexity"
version = "1.0.0"
description = "Code complexity analysis for Griffonner"

[project.entry-points."griffonner.processors"]
complexity_analyser = "griffonner_complexity:ComplexityProcessor"
metadata_adder = "griffonner_complexity:metadata_processor"

[project.entry-points."griffonner.filters"]
format_signature = "griffonner_complexity.filters:format_signature"
complexity_badge = "griffonner_complexity.filters:complexity_badge"
to_json = "griffonner_complexity.filters:to_json"
doc_link = "griffonner_complexity.filters:doc_link"
gitlab_format = "griffonner_complexity.filters:gitlab_formatter"
```

### Using setup.py

Alternative entry points configuration:

```python
from setuptools import setup

setup(
    name="griffonner-complexity",
    version="1.0.0",
    packages=["griffonner_complexity"],
    entry_points={
        "griffonner.processors": [
            "complexity_analyser = griffonner_complexity:ComplexityProcessor",
        ],
        "griffonner.filters": [
            "format_signature = griffonner_complexity.filters:format_signature",
            "complexity_badge = griffonner_complexity.filters:complexity_badge",
        ],
    },
)
```

## Testing plugins

### Testing processors

```python
import pytest
from unittest.mock import Mock
from your_plugin import ComplexityProcessor

def test_complexity_processor():
    processor = ComplexityProcessor()
    
    # Mock Griffe object
    mock_func = Mock()
    mock_func.kind.value = "function"
    mock_func.name = "test_function"
    mock_func.source = "def test_function():\n    if True:\n        return"
    
    context = {"processor_config": {"complexity_threshold": 5}}
    
    result_obj, result_context = processor.process(mock_func, context)
    
    assert result_obj is mock_func  # Object unchanged
    assert "complexity" in result_context
    assert result_context["complexity"]["score"] > 0
    
def test_complexity_threshold():
    processor = ComplexityProcessor()
    mock_func = Mock()
    mock_func.kind.value = "function"
    mock_func.source = "def complex():\n" + "if True:\n" * 10  # High complexity
    
    context = {"processor_config": {"complexity_threshold": 3}}
    
    _, result_context = processor.process(mock_func, context)
    
    assert "warnings" in result_context
    assert len(result_context["warnings"]) > 0
```

### Testing filters

```python
def test_format_signature():
    from your_plugin.filters import format_signature
    
    # Mock signature object
    mock_param = Mock()
    mock_param.name = "param1"
    mock_param.annotation = "str"
    mock_param.default = None
    
    mock_signature = Mock()
    mock_signature.parameters = [mock_param]
    
    result = format_signature(mock_signature)
    assert "param1: str" in result

def test_complexity_badge():
    from your_plugin.filters import complexity_badge
    
    assert complexity_badge(3) == "🟢 Simple (score: 3)"
    assert complexity_badge(7) == "🟡 Moderate (score: 7)"
    assert complexity_badge(15) == "🔴 Complex (score: 15)"
    
    # Test with dict input
    complexity_data = {"score": 8, "level": "moderate"}
    result = complexity_badge(complexity_data)
    assert "🟡 Moderate (score: 8)" == result
```

## Publishing plugins

### Package structure

```
griffonner-complexity/
├── griffonner_complexity/
│   ├── __init__.py          # Exports ComplexityProcessor
│   ├── processor.py         # ComplexityProcessor class
│   └── filters.py           # Filter functions
├── tests/
│   ├── test_processor.py
│   └── test_filters.py
├── pyproject.toml           # Entry points configuration
├── README.md
└── LICENSE
```

### PyPI publishing

```shell
# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*

# Install from PyPI
pip install griffonner-complexity
```

### Testing installation

```shell
# Install in development mode
pip install -e .

# Check plugin is discovered
griffonner plugins

# Test with actual documentation
griffonner generate test-docs/ --output output/
```

## Best practices

### Naming conventions

- **Packages**: `griffonner-{purpose}` (e.g., `griffonner-complexity`)
- **Processors**: `{purpose}_{type}` (e.g., `complexity_analyser`)  
- **Filters**: `{action}_{object}` (e.g., `format_signature`)

### Error handling

```python
def process(self, griffe_obj, context):
    try:
        # Your processing logic
        result = self.complex_analysis(griffe_obj)
        context["analysis"] = result
    except Exception as e:
        # Log error but don't crash generation
        import logging
        logging.warning(f"Analysis failed for {griffe_obj.name}: {e}")
        context["analysis"] = {"error": str(e)}
    
    return griffe_obj, context
```

### Configuration validation

```python
def process(self, griffe_obj, context):
    config = context.get("processor_config", {})
    
    # Validate configuration
    threshold = config.get("threshold")
    if threshold is not None and not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be a number")
    
    threshold = threshold or 10  # Default value
    
    # Continue processing...
```

### Documentation

Include clear documentation:

```python
class ComplexityProcessor(BaseProcessor):
    """Analyse code complexity and add metrics to template context.
    
    Configuration options:
    - complexity_threshold (int): Threshold for complexity warnings (default: 10)
    - include_details (bool): Include detailed complexity breakdown (default: False)
    
    Context additions:
    - complexity: Dict with 'score' and 'level' keys
    - warnings: List of high-complexity function names (if threshold exceeded)
    """
```

## See also

- [Bundle development](bundle-development.md) - Creating plugin bundles
- [Using processors](../plugins/using-processors.md) - How to use processors
- [Using filters](../plugins/using-filters.md) - How to use filters
- [Managing plugins](../plugins/managing-plugins.md) - Installing and discovering plugins