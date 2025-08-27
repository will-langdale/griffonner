# CLI reference

Complete reference for all Griffonner commands and options.

## Usage

```
griffonner [OPTIONS] COMMAND [ARGS]...
```

Griffonner is a template-first Python documentation generator that gets out of your way.

## Commands

### `generate`

Generate documentation from source files. Files with frontmatter are processed using templates, while files without frontmatter are copied directly to the output (passthrough).

Configuration is loaded from `griffonner.yml`/`griffonner.yaml` or `pyproject.toml`. CLI arguments override configuration file values.

```
griffonner generate [OPTIONS] SOURCE
```

**Arguments:**

- `SOURCE` - Source file or directory containing files (with or without frontmatter)

**Options:**

- `--output, -o PATH` - Output directory (default: `docs/output`)
- `--template-dir, -t PATH` - Additional template directories (can be used multiple times)
- `--local-plugins, -l TEXT` - Python modules containing local plugins (can be used multiple times)
- `--ignore TEXT` - Glob patterns to ignore in source directory (can be used multiple times)
- `--help` - Show help message

**Examples:**

```shell
# Generate from a single file
griffonner generate docs/pages/api.md

# Generate from a directory
griffonner generate docs/pages/

# Custom output directory
griffonner generate docs/pages/ --output build/docs

# Additional template directories
griffonner generate docs/pages/ --template-dir custom-templates/ --template-dir shared-templates/

# With local plugins
griffonner generate docs/pages/ --local-plugins myproject.docs_plugins
griffonner generate docs/pages/ --local-plugins myproject.filters --local-plugins myproject.processors

# Ignore specific file patterns
griffonner generate docs/pages/ --ignore "*.tmp" --ignore "*.pyc"

# Ignore directories and file patterns
griffonner generate docs/pages/ --ignore "__pycache__/*" --ignore "build/*" --ignore "*.log"

# Combined options
griffonner generate docs/pages/ --output build/docs --ignore "*.tmp" --ignore ".git/*"
```

### `watch`

Watch source directory for changes and regenerate documentation automatically.

Configuration is loaded from `griffonner.yml`/`griffonner.yaml` or `pyproject.toml`. CLI arguments override configuration file values.

```
griffonner watch [OPTIONS] SOURCE
```

**Arguments:**

- `SOURCE` - Source directory to watch for changes

**Options:**

- `--output, -o PATH` - Output directory (default: `docs/output`)
- `--template-dir, -t PATH` - Additional template directories (can be used multiple times)
- `--local-plugins, -l TEXT` - Python modules containing local plugins (can be used multiple times)
- `--ignore TEXT` - Glob patterns to ignore in source directory (can be used multiple times)
- `--help` - Show help message

**Examples:**

```shell
# Basic watch mode
griffonner watch docs/pages/

# Watch with custom output
griffonner watch docs/pages/ --output build/docs

# Watch with additional templates
griffonner watch docs/pages/ --template-dir custom-templates/

# Watch with local plugins
griffonner watch docs/pages/ --local-plugins myproject.docs_plugins

# Watch with ignore patterns
griffonner watch docs/pages/ --ignore "*.tmp" --ignore "__pycache__/*"

# Combined watch options
griffonner watch docs/pages/ --output build/docs --ignore "build/*" --ignore "*.log"
```

**Behaviour:**

- Monitors all files in the source directory for changes
- Processes files with frontmatter using templates, copies files without frontmatter directly (passthrough)
- Automatically creates output directories if they don't exist
- Shows real-time feedback when files are regenerated
- Stops with Ctrl+C

### `templates`

List available templates in the search path.

Configuration is loaded from `griffonner.yml`/`griffonner.yaml` or `pyproject.toml`. CLI arguments override configuration file values.

```
griffonner templates [OPTIONS]
```

**Options:**

- `--template-dir, -t PATH` - Template directories to search (can be used multiple times)
- `--pattern, -p TEXT` - Pattern to match templates (default: `**/*.jinja2`)
- `--help` - Show help message

**Examples:**

```shell
# List all templates
griffonner templates

# Search custom directories
griffonner templates --template-dir custom-templates/

# Filter by pattern
griffonner templates --pattern "**/module*"
griffonner templates --pattern "python/default/*"
```

**Template search order:**

1. Directories specified with `--template-dir`
2. `docs/templates/` (if it exists)
3. `templates/` (if it exists)
4. Built-in templates (shipped with Griffonner)

### `validate`

Validate template syntax and structure.

Configuration is loaded from `griffonner.yml`/`griffonner.yaml` or `pyproject.toml`. CLI arguments override configuration file values.

```
griffonner validate [OPTIONS] TEMPLATE_PATH
```

**Arguments:**

- `TEMPLATE_PATH` - Relative path to template (e.g., `python/default/module.md.jinja2`)

**Options:**

- `--template-dir, -t PATH` - Template directories to search (can be used multiple times)
- `--help` - Show help message

**Examples:**

```shell
# Validate a built-in template
griffonner validate python/default/module.md.jinja2

# Validate a custom template
griffonner validate --template-dir custom-templates/ my-custom/template.md.jinja2
```

**What is validated:**

- Jinja2 syntax correctness
- Template can be loaded and parsed
- No undefined variables in template logic

### `plugins`

List installed plugins and their details.

Configuration is loaded from `griffonner.yml`/`griffonner.yaml` or `pyproject.toml`. CLI arguments override configuration file values.

```
griffonner plugins [OPTIONS]
```

**Options:**

- `--local-plugins, -l TEXT` - Python modules containing local plugins (can be used multiple times)
- `--help` - Show help message

**Examples:**

```shell
# List all installed plugins
griffonner plugins

# Include local plugins
griffonner plugins --local-plugins myproject.docs_plugins
```

**Output includes:**

- Plugin name and type (processor or filter)
- Plugin source (entry point package or local module)
- Brief description (if available)

**Local plugins:**

Local plugins are loaded from Python modules you specify. They appear with their module path in the plugin list (e.g., `myproject.docs_plugins.my_filter`).

### `bundle`

Show information about installed plugin bundles.

Configuration is loaded from `griffonner.yml`/`griffonner.yaml` or `pyproject.toml` for verbose setting.

```
griffonner bundle [OPTIONS] [BUNDLE_NAME]
```

**Arguments:**

- `BUNDLE_NAME` - Name of specific bundle to show (optional)

**Options:**

- `--help` - Show help message

**Examples:**

```shell
# List all available bundles
griffonner bundle

# Show details for a specific bundle
griffonner bundle gitlab-wiki
```

**Bundle details include:**

- Bundle name, version, and description
- Included processors and filters
- Template paths provided by the bundle
- Example usage

## Global options

These options are available for all commands:

- `--verbose, -v` - Enable verbose logging for debugging
- `--help` - Show help message and exit

## Exit codes

- `0` - Success
- `1` - Error (invalid arguments, template not found, generation failed, etc.)

## Configuration

### Template directories

Griffonner searches for templates in this order:

1. Additional directories specified with `--template-dir` option
2. `docs/templates/` in the current directory
3. `templates/` in the current directory
4. Built-in templates shipped with Griffonner

### Environment variables

Currently, Griffonner doesn't use any environment variables for configuration.

### Configuration files

Griffonner supports configuration files to avoid repeating CLI arguments and set project defaults.

For complete information about configuration files, file formats, all available options, precedence rules, and examples, see the dedicated **[Configuration guide](configuration.md)**.

**Quick summary:**
- **File formats**: `griffonner.yml`, `griffonner.yaml`, or `pyproject.toml` with `[tool.griffonner]` section
- **Discovery order**: `.yml` → `.yaml` → `pyproject.toml`
- **Precedence**: Built-in defaults → Configuration file → CLI arguments → Frontmatter (Griffe only)
- **Key feature**: Set default Griffe options for your entire project

**CLI arguments always override configuration file values.**

## Output structure

When generating documentation:

- Output files maintain the relative directory structure of source files
- The `filename` specified in frontmatter determines the final filename
- Directories are created automatically as needed

Example:

```
Source: docs/pages/api/core.md
Output: docs/output/api/core-reference.md  # if filename: "core-reference.md"
```

## Error handling

Griffonner provides helpful error messages for common issues:

### Template not found

```
❌ Generation failed: Template not found: custom/missing.md.jinja2

Did you mean one of these?
  - python/default/module.md.jinja2
  - python/default/class.md.jinja2

Available template sets:
  - python/default/
```

### Invalid frontmatter

```
❌ Generation failed: Invalid frontmatter in docs/pages/api.md
Missing required field: template
```

### Module import errors

```
❌ Generation failed: Could not import module: mypackage.nonexistent
Ensure the module is installed and importable
```

## Tips

### Debugging

- Use `--verbose` or `-v` to enable detailed logging for troubleshooting
- Use `griffonner templates` to verify template availability
- Use `griffonner validate` to check template syntax
- Use `griffonner plugins` to check installed plugins
- Use `griffonner bundle` to verify bundle components
- Check file paths are relative to the correct directory

**Verbose mode provides detailed information about:**

- Griffe object loading and parsing
- Template discovery and rendering
- Plugin loading and processor execution
- Frontmatter parsing and validation
- File system operations in watch mode
- Context preparation and variable resolution

**Examples with verbose mode:**

```shell
# Debug generation issues
griffonner generate docs/pages/ --verbose

# Debug template loading
griffonner templates --verbose

# Debug watch mode
griffonner watch docs/pages/ --verbose
```

### Ignore patterns

The `--ignore` option allows you to exclude files and directories from processing using glob patterns. This is useful for avoiding temporary files, build artifacts, and version control directories.

**Pattern syntax:**
- `*.ext` - Ignores all files with the specified extension
- `dirname/*` - Ignores all files within a directory
- `**/pattern` - Recursively matches pattern at any depth
- `path/to/file` - Ignores specific file path

**Common examples:**
```shell
# Ignore common temporary and cache files
--ignore "*.tmp" --ignore "*.pyc" --ignore "*.log"

# Ignore build and cache directories
--ignore "build/*" --ignore "__pycache__/*" --ignore ".git/*"

# Ignore Node.js and Python artifacts
--ignore "node_modules/*" --ignore "dist/*" --ignore "*.egg-info/*"
```

**Behaviour:**
- Patterns are matched against file paths relative to the source directory
- Pattern matching is case-sensitive
- Files matching any ignore pattern are completely excluded from processing
- In watch mode, ignored files won't trigger regeneration when changed
- Multiple `--ignore` flags can be used to specify multiple patterns

### Performance

- Watch mode monitors all file types and processes both frontmatter and regular files
- Files with frontmatter are generated using templates, files without are copied directly
- Generation is incremental - only changed files are regenerated in watch mode
- Using ignore patterns can significantly improve performance by excluding unnecessary files

### Workflow

1. Start with `griffonner templates` to see available options
2. Check `griffonner plugins` for installed processors and filters
3. Use `griffonner bundle` to explore available bundles
4. Create source files with frontmatter
5. Set up local plugins if needed with `--local-plugins`
6. Configure ignore patterns to exclude unwanted files with `--ignore`
7. Test with `griffonner generate` for single runs
8. Use `griffonner watch` for development with live reload
9. Validate custom templates with `griffonner validate`