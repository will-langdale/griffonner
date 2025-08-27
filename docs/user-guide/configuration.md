# Configuration

Complete guide to configuring Griffonner using configuration files.

## Overview

Configuration files allow you to set default options for Griffonner commands without repeating CLI arguments every time. This is particularly useful for:

- **Project consistency**: Ensure all team members use the same settings
- **Default Griffe options**: Set project-wide Griffe configuration that applies to all files
- **Simplified commands**: Run `griffonner generate docs/` instead of long command lines
- **Environment-specific settings**: Different configurations for development, testing, production

Configuration files are completely optional - Griffonner works perfectly without them.

## Configuration file formats

Griffonner supports two configuration file formats:

### YAML configuration

Create a `griffonner.yml` or `griffonner.yaml` file in your project root:

```yaml
# Basic settings
output_dir: "build/docs"
verbose: true

# Template and plugin settings
template_dirs:
  - "custom-templates/"
  - "shared-templates/"
local_plugins:
  - "myproject.docs_plugins"
  - "myproject.processors"

# File processing
ignore:
  - "*.tmp"
  - "__pycache__/*"
  - "build/*"
  - ".git/*"

# Default Griffe configuration
griffe:
  loader:
    allow_inspection: true
    store_source: false
    docstring_parser: "google"
    load:
      submodules: true
      find_stubs_package: false
    resolve_aliases:
      external: false
      implicit: false
      max_iterations: 10

# Template discovery
templates:
  pattern: "**/*.jinja2"
```

### TOML configuration

Add a `[tool.griffonner]` section to your `pyproject.toml`:

```toml
[tool.griffonner]
output_dir = "build/docs"
verbose = true
template_dirs = ["custom-templates/", "shared-templates/"]
local_plugins = ["myproject.docs_plugins"]
ignore = ["*.tmp", "__pycache__/*", "build/*"]

# Default Griffe configuration
[tool.griffonner.griffe.loader]
allow_inspection = true
store_source = false
docstring_parser = "google"

[tool.griffonner.griffe.loader.load]
submodules = true
find_stubs_package = false

[tool.griffonner.griffe.loader.resolve_aliases]
external = false
implicit = false
max_iterations = 10

[tool.griffonner.templates]
pattern = "**/*.jinja2"
```

## Configuration options

All configuration options are optional and have sensible defaults.

### Core settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_dir` | `string` | `"docs/output"` | Directory where generated files are written |
| `verbose` | `boolean` | `false` | Enable verbose logging for debugging |

### Template and plugin settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `template_dirs` | `array` | `[]` | Additional directories to search for templates |
| `local_plugins` | `array` | `[]` | Python modules containing local plugins (filters/processors) |

### File processing

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ignore` | `array` | `[]` | Glob patterns for files to ignore during generation |

### Template discovery

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `templates.pattern` | `string` | `"**/*.jinja2"` | Pattern for finding template files |

### Default Griffe configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `griffe` | `object` | `{}` | Default Griffe options applied to all files (completely permissive) |

The `griffe` section is the most powerful feature - it sets project-wide defaults for Griffe parsing that apply to all files unless overridden in individual file frontmatter.

## File discovery order

Griffonner searches for configuration files in this order (first found wins):

1. `griffonner.yml` in current directory
2. `griffonner.yaml` in current directory
3. `pyproject.toml` with `[tool.griffonner]` section in current directory

If no configuration file is found, built-in defaults are used.

## Configuration precedence

Settings are applied in this order, with later sources overriding earlier ones:

1. **Built-in defaults** (lowest priority)
2. **Configuration file** (`griffonner.yml` > `griffonner.yaml` > `pyproject.toml`)
3. **CLI arguments** (override config file settings)
4. **Frontmatter `griffe:` section** (highest priority, applies only to Griffe options)

### Example precedence

Given this configuration file:
```yaml
output_dir: "build/docs"
verbose: true
griffe:
  loader:
    allow_inspection: true
    docstring_parser: "google"
```

And this command:
```shell
griffonner generate docs/ --output custom-output/ --verbose false
```

The final settings will be:
- `output_dir`: `"custom-output/"` (CLI override)
- `verbose`: `false` (CLI override)
- `griffe.loader.allow_inspection`: `true` (from config)
- `griffe.loader.docstring_parser`: `"google"` (from config)

## Default Griffe configuration

The `griffe` section in configuration files provides **default Griffe settings** for your entire project. This is the most important feature for reducing repetition.

### How it works

1. **Set defaults once**: Configure Griffe options in your config file
2. **Apply everywhere**: These settings apply to all files automatically
3. **Override when needed**: Individual files can override via frontmatter `griffe:` section
4. **Deep merging**: Frontmatter settings are merged with config defaults, not replaced

### Completely unopinionated

The `griffe` section accepts any valid Griffe configuration - Griffonner doesn't validate or restrict the options. This means:

- Any Griffe loader option is supported
- Any Griffe method call configuration is supported
- You control exactly how Griffe parses your code
- Future Griffe API changes are automatically supported

### Practical example

**Configuration file sets project defaults:**
```yaml
griffe:
  loader:
    allow_inspection: true
    store_source: false
    docstring_parser: "google"
    load:
      submodules: true
```

**Most files inherit these defaults automatically** (no frontmatter needed).

**Special files can override specific settings:**
```yaml
---
template: "python/default/module.md.jinja2"
output:
  - filename: "internal-api.md"
    griffe_target: "mypackage.internal"
griffe:
  loader:
    allow_inspection: false  # Override: don't inspect this module
    # All other settings inherited from config file
---
```

**Result**: The file gets `allow_inspection: false` but keeps `store_source: false`, `docstring_parser: "google"`, and `load.submodules: true` from the config.

### Common Griffe configurations

**Basic Python project:**
```yaml
griffe:
  loader:
    allow_inspection: true
    docstring_parser: "google"
    load:
      submodules: true
```

**Strict static analysis only:**
```yaml
griffe:
  loader:
    allow_inspection: false
    store_source: true
    load:
      submodules: false
```

**Complex project with alias resolution:**
```yaml
griffe:
  loader:
    allow_inspection: true
    docstring_parser: "numpy"
    load:
      submodules: true
      find_stubs_package: true
    resolve_aliases:
      external: true
      implicit: true
      max_iterations: 5
```

## Examples and workflows

### Simple project setup

For a basic Python project, create `griffonner.yml`:

```yaml
output_dir: "docs/generated"
verbose: true
ignore:
  - "*.pyc"
  - "__pycache__/*"
  - "tests/*"

griffe:
  loader:
    docstring_parser: "google"
    load:
      submodules: true
```

Then run simplified commands:
```shell
# Uses all config settings
griffonner generate docs/pages/

# Override output directory
griffonner generate docs/pages/ --output docs/api/
```

### Multi-environment setup

Use different configurations for different environments:

**Development (`griffonner.yml`):**
```yaml
output_dir: "docs/dev"
verbose: true
griffe:
  loader:
    allow_inspection: true    # Runtime introspection OK in dev
    store_source: true       # Include source code
```

**Production (`griffonner.prod.yml`):**
```yaml
output_dir: "docs/prod"
verbose: false
griffe:
  loader:
    allow_inspection: false  # Static analysis only
    store_source: false     # Exclude source code
```

Then specify the config file:
```shell
# Development
griffonner generate docs/pages/

# Production (explicit config)
cp griffonner.prod.yml griffonner.yml
griffonner generate docs/pages/
```

### Migration from CLI-only

**Before** (repetitive CLI commands):
```shell
griffonner generate docs/pages/ --output build/docs --template-dir custom-templates/ --local-plugins myproject.plugins --ignore "*.tmp" --ignore "__pycache__/*" --verbose
griffonner watch docs/pages/ --output build/docs --template-dir custom-templates/ --local-plugins myproject.plugins --ignore "*.tmp" --ignore "__pycache__/*" --verbose
```

**After** (create `griffonner.yml`):
```yaml
output_dir: "build/docs"
template_dirs: ["custom-templates/"]
local_plugins: ["myproject.plugins"]
ignore: ["*.tmp", "__pycache__/*"]
verbose: true
```

**New commands** (much simpler):
```shell
griffonner generate docs/pages/
griffonner watch docs/pages/
```

### Plugin-heavy project

For projects using many plugins:

```yaml
output_dir: "docs/api"
template_dirs:
  - "templates/custom/"
  - "templates/shared/"
  - "node_modules/@company/doc-templates/"

local_plugins:
  - "myproject.doc_plugins"
  - "myproject.doc_filters"
  - "myproject.doc_processors"

ignore:
  - "*.tmp"
  - "*.log"
  - "__pycache__/*"
  - "node_modules/*"
  - ".git/*"
  - "build/*"
  - "dist/*"

griffe:
  loader:
    allow_inspection: true
    docstring_parser: "google"
    load:
      submodules: true
      find_stubs_package: true
```

## Integration with other documentation

### CLI reference

For detailed information about CLI arguments that correspond to configuration options, see [CLI reference](cli-reference.md).

Configuration file options have the same names as CLI arguments:
- `--output` → `output_dir`
- `--template-dir` → `template_dirs`
- `--local-plugins` → `local_plugins`
- `--ignore` → `ignore`
- `--verbose` → `verbose`

### Frontmatter reference

The `griffe` section in configuration files uses the same structure as the `griffe:` section in frontmatter. For detailed information about Griffe options, see [Frontmatter reference](frontmatter-reference.md#griffe).

### Watch mode

Configuration files work seamlessly with watch mode. See [Watch mode](watch-mode.md) for development workflows using configuration files.

## Troubleshooting

### Configuration not loading

**Check file location**: Configuration files must be in the current working directory where you run `griffonner` commands.

**Check file format**: 
- YAML files must be valid YAML syntax
- TOML files must have the `[tool.griffonner]` section

**Use verbose mode** to see configuration loading:
```shell
griffonner generate docs/ --verbose
```

### TOML section not found

If using `pyproject.toml`, ensure you have the `[tool.griffonner]` section:

```toml
# ❌ Wrong - no [tool.griffonner] section
output_dir = "docs/"

# ✅ Correct
[tool.griffonner]
output_dir = "docs/"
```

### Griffe options not working

**Check option names**: Griffe options must match the current Griffe API. Refer to [Griffe documentation](https://mkdocstrings.github.io/griffe/) for available options.

**Test with frontmatter first**: If you're unsure about a Griffe option, test it in a single file's frontmatter before adding to config.

**Use verbose logging** to see what Griffe options are being applied:
```shell
griffonner generate docs/single-file.md --verbose
```