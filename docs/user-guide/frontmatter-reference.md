# Frontmatter reference

Complete reference for YAML frontmatter configuration in Griffonner source files.

## Overview

Frontmatter is YAML configuration at the start of markdown files that tells Griffonner how to generate documentation. It's delimited by triple dashes (`---`) and must be valid YAML.

```markdown
---
template: "python/default/module.md.jinja2"
output:
  - filename: "api-reference.md"
    griffe_target: "mypackage.api"
custom_vars:
  title: "API Documentation"
---

# Your markdown content here
```

## Required fields

### `template`

**Type**: `string`  
**Required**: Yes

Path to the Jinja2 template file, relative to template search directories.

```yaml
template: "python/default/module.md.jinja2"
template: "custom/my-template.md.jinja2"
template: "rst/sphinx-style/module.rst.jinja2"
```

Griffonner searches for templates in:
1. Directories specified with `--template-dir`
2. `docs/templates/` (if it exists)
3. `templates/` (if it exists)  
4. Built-in templates

### `output`

**Type**: `array` of output configurations  
**Required**: Yes

Defines what files to generate from this source file.

```yaml
output:
  - filename: "api-reference.md"
    griffe_target: "mypackage.api"
```

Each output entry requires:
- `filename`: Output filename  
- `griffe_target`: Python module/object to parse

## Optional fields

### `custom_vars`

**Type**: `object`  
**Default**: `{}`

Custom variables available in templates as `{{ custom_vars.variable_name }}`.

```yaml
custom_vars:
  title: "API Documentation"
  version: "1.2.0"
  emoji: "📚"
  show_private: false
  categories:
    - "Core"
    - "Utilities"
```

### `processors`

**Type**: `object`  
**Default**: `{}`

Configure which processors to run and their settings.

```yaml
processors:
  enabled:
    - "complexity_analyser" 
    - "metadata_extractor"
  disabled:
    - "type_checker"
  config:
    complexity_threshold: 10
    include_private: false
```

#### `processors.enabled`

**Type**: `array` of `string`  
**Default**: `[]`

List of processors to enable for this generation.

```yaml
processors:
  enabled:
    - "complexity_analyser"
    - "custom_processor" 
    - "bundle_name.processor_name"  # From plugin bundles
```

#### `processors.disabled`

**Type**: `array` of `string`  
**Default**: `[]`

List of processors to explicitly disable (overrides enabled list).

```yaml
processors:
  enabled: ["*"]  # Enable all available
  disabled: 
    - "slow_processor"
    - "experimental_feature"
```

#### `processors.config`

**Type**: `object`  
**Default**: `{}`

Configuration passed to processors. Structure depends on specific processors.

```yaml
processors:
  config:
    # Configuration for complexity_analyser
    complexity_threshold: 15
    include_details: true
    
    # Configuration for metadata_extractor  
    extract_todos: true
    scan_comments: false
```

### `griffe_options`

**Type**: `object`  
**Default**: `{}`

Options passed directly to Griffe for code parsing.

```yaml
griffe_options:
  include_private: false
  show_source: true
  docstring_style: "google"
  follow_imports: true
```

Common options:
- `include_private`: Include private members (leading underscore)
- `show_source`: Include source code in parsed objects
- `docstring_style`: Docstring parsing style (`"google"`, `"numpy"`, `"sphinx"`)
- `follow_imports`: Parse imported modules

## Output configuration

The `output` array defines what files to generate. Each entry creates one output file.

### Single output

```yaml
output:
  - filename: "api.md"
    griffe_target: "mypackage"
```

### Multiple outputs

Generate multiple files from one source:

```yaml
output:
  - filename: "core-api.md"
    griffe_target: "mypackage.core"
  - filename: "utils-api.md" 
    griffe_target: "mypackage.utils"
  - filename: "complete-api.md"
    griffe_target: "mypackage"
```

### Per-output options

Each output can have its own Griffe options:

```yaml
output:
  - filename: "public-api.md"
    griffe_target: "mypackage"
    griffe_options:
      include_private: false
  - filename: "internal-api.md"
    griffe_target: "mypackage"  
    griffe_options:
      include_private: true
```

## Complete example

```yaml
---
template: "python/default/module.md.jinja2"

output:
  - filename: "core-api.md"
    griffe_target: "myproject.core"
    griffe_options:
      include_private: false
      show_source: true
  - filename: "utils-api.md"
    griffe_target: "myproject.utils"

processors:
  enabled:
    - "complexity_analyser"
    - "metadata_extractor"
  config:
    complexity_threshold: 8
    extract_todos: true
    include_private: false

custom_vars:
  project_name: "My Project"
  version: "2.1.0"
  emoji: "🛠️"
  maintainer: "Development Team"
  categories:
    - "Core APIs"
    - "Utility Functions"
  show_examples: true
  api_base_url: "https://api.example.com"

griffe_options:
  docstring_style: "google"
  follow_imports: false
---

# API Documentation

This documentation is generated from the latest codebase.
```

## Template context

The frontmatter creates template context variables:

```jinja2
{# Template has access to: #}
{{ obj }}               {# Griffe object from griffe_target #}
{{ custom_vars }}       {# All custom_vars as a dict #}
{{ source_content }}    {# Markdown content after frontmatter #}
{{ source_path }}       {# Path to source file #}

{# Custom variables directly accessible: #}
{{ custom_vars.title }}
{{ custom_vars.version }}
{{ custom_vars.emoji }}

{# Processor results in context: #}
{{ complexity }}        {# If complexity_analyser processor ran #}
{{ metadata }}          {# If metadata_extractor processor ran #}
```

## Validation

Griffonner validates frontmatter when generating documentation:

### Required field errors

```
❌ Generation failed: Invalid frontmatter in docs/pages/api.md
Missing required field: template
```

### YAML syntax errors

```
❌ Generation failed: Invalid frontmatter in docs/pages/api.md  
YAML syntax error: expected <block end>, but found '<scalar>'
```

### Template not found

```
❌ Generation failed: Template not found: custom/missing.md.jinja2

Did you mean one of these?
  - python/default/module.md.jinja2
  - python/default/class.md.jinja2
```

### Module import errors

```
❌ Generation failed: Could not import module: nonexistent.module
Ensure the module is installed and importable
```

## Best practices

### Organisation

Keep frontmatter organised and documented:

```yaml
---
# Template configuration
template: "python/default/module.md.jinja2"

# Output files
output:
  - filename: "core-api.md"
    griffe_target: "myproject.core"

# Processing configuration  
processors:
  enabled: ["complexity_analyser"]
  config:
    complexity_threshold: 10

# Custom template variables
custom_vars:
  title: "Core API"
  category: "Internal APIs"
---
```

### Reusable configuration

For similar files, extract common configuration:

```yaml
# Common base configuration
processors: &default_processors
  enabled: ["complexity_analyser", "metadata_extractor"] 
  config:
    complexity_threshold: 8
    include_private: false

custom_vars: &default_vars
  project_name: "My Project"
  maintainer: "Dev Team"
```

Then reference in files:

```yaml
---
template: "python/default/module.md.jinja2"
processors: *default_processors
custom_vars: 
  <<: *default_vars
  title: "Core Module"  # Override specific values
output:
  - filename: "core.md"
    griffe_target: "myproject.core"
---
```

### Environment-specific configuration

Use YAML anchors for different environments:

```yaml
# Development configuration
dev_griffe: &dev_griffe
  include_private: true
  show_source: true

# Production configuration  
prod_griffe: &prod_griffe
  include_private: false
  show_source: false
```

### Validation workflow

1. Use `griffonner validate` to check templates
2. Test with small modules first
3. Use `griffonner generate` single files before batch processing
4. Enable `griffonner watch` for development iterations

## See also

- [CLI reference](cli-reference.md) - Command-line options and validation
- [Template development](../template-guides/template-development.md) - Creating custom templates
- [Using processors](../plugins/using-processors.md) - Processor configuration and usage
- [Watch mode](watch-mode.md) - Development workflow with frontmatter