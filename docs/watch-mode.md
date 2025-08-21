# Watch mode

Learn how to use Griffonner's watch mode for efficient development workflows.

## Overview

Watch mode monitors your source files for changes and automatically regenerates documentation when files are modified. This provides a live development experience similar to modern web development tools.

## Basic usage

Start watching a directory:

```shell
griffonner watch docs/pages/
```

This will:

1. Monitor all `.md` and `.markdown` files in `docs/pages/`
2. Check files for valid frontmatter
3. Regenerate documentation when files change
4. Show real-time feedback in the terminal

## Command options

### Output directory

Specify where generated files should go:

```shell
griffonner watch docs/pages/ --output docs/generated
```

### Additional template directories

Include custom template directories:

```shell
griffonner watch docs/pages/ --template-dir custom-templates/
```

Multiple template directories:

```shell
griffonner watch docs/pages/ \
  --template-dir custom-templates/ \
  --template-dir shared-templates/
```

## What gets watched

Watch mode monitors:

- **File types**: `.md` and `.markdown` files only
- **Scope**: All files recursively in the source directory
- **Filtering**: Only processes files with valid frontmatter
- **Events**: File modifications and new file creation

Files without frontmatter are ignored, so you can have regular markdown files alongside Griffonner source files.

## Development workflow

### 1. Initial setup

Create your project structure:

```shell
mkdir my-docs
cd my-docs
mkdir -p docs/pages docs/output
```

### 2. Create source files

Create `docs/pages/api.md`:

```markdown
---
template: "python/default/module.md.jinja2"
output:
  - filename: "api-reference.md"
    griffe_target: "mypackage"
---

# API documentation

This will be combined with generated content.
```

### 3. Start watch mode

```shell
griffonner watch docs/pages/ --output docs/output
```

You'll see:

```
👀 Watching /path/to/docs/pages for changes...
📂 Output directory: /path/to/docs/output
Press Ctrl+C to stop
```

### 4. Make changes

Edit `docs/pages/api.md` and save. You'll immediately see:

```
🔄 Regenerated 1 files from api.md:
  📄 api-reference.md
```

### 5. Template development

When developing custom templates, watch mode is invaluable:

1. Create a custom template
2. Reference it in your frontmatter
3. Watch mode will show template errors immediately
4. Iterate quickly on template design

## Real-time feedback

Watch mode provides detailed feedback:

### Successful regeneration

```
🔄 Regenerated 2 files from module-docs.md:
  📄 core-api.md
  📄 utils-api.md
```

### Template errors

```
❌ Failed to regenerate docs/pages/api.md: Template not found: custom/missing.md.jinja2

Did you mean one of these?
  - python/default/module.md.jinja2
  - python/default/class.md.jinja2
```

### Frontmatter errors

```
❌ Failed to regenerate docs/pages/broken.md: Invalid frontmatter
Missing required field: template
```

### Import errors

```
❌ Failed to regenerate docs/pages/api.md: Could not import module: nonexistent.module
Ensure the module is installed and importable
```

## Integration with editors

### VS Code

VS Code users can enhance their workflow:

1. **Split layout**: Source files on left, output directory on right
2. **Auto-save**: Enable auto-save for immediate regeneration
3. **Terminal**: Keep watch mode running in integrated terminal
4. **Extensions**: Use markdown preview for generated files

### Other editors

Most editors support:

- **Auto-save**: Triggers regeneration on file save
- **File watchers**: Some editors can trigger custom commands
- **Split panes**: View source and generated files side-by-side

## Multiple source directories

Watch mode monitors a single source directory, but you can run multiple instances:

```shell
# Terminal 1
griffonner watch docs/api/ --output docs/output

# Terminal 2  
griffonner watch docs/guides/ --output docs/output
```

Or organise with a single source directory:

```
docs/
├── pages/
│   ├── api/
│   │   ├── core.md
│   │   └── utils.md
│   └── guides/
│       ├── installation.md
│       └── usage.md
└── output/
```

Then watch the entire `pages/` directory:

```shell
griffonner watch docs/pages/ --output docs/output
```

## Performance considerations

### File system events

Watch mode uses Python's `watchdog` library for efficient file monitoring:

- **Cross-platform**: Works on Linux, macOS, and Windows
- **Efficient**: Only processes actual file changes
- **Recursive**: Monitors subdirectories automatically

### Large projects

For projects with many files:

- Only files with frontmatter are processed
- Generation is incremental (only changed files)
- Template loading is cached between runs

### Network filesystems

Watch mode works on network filesystems, but performance may vary:

- **Local filesystems**: Best performance
- **Network drives**: May have slight delays
- **Cloud sync**: Depends on sync behaviour

## Troubleshooting

### Watch mode not starting

**Directory doesn't exist:**
```
❌ Watch failed: Source directory not found: /path/to/nonexistent
```

**Not a directory:**
```
❌ Watch failed: Source path is not a directory: /path/to/file.md
```

### Files not regenerating

Check these common issues:

1. **File type**: Only `.md` and `.markdown` files are monitored
2. **Frontmatter**: File must have valid frontmatter to be processed
3. **Directory**: File must be within the watched directory
4. **Permissions**: Ensure files are readable

### Template errors

Template errors are shown immediately:

```
❌ Failed to regenerate api.md: Template syntax error in custom/broken.md.jinja2: unexpected '}'
```

Use `griffonner validate` to check templates before using them:

```shell
griffonner validate custom/my-template.md.jinja2
```

### Memory usage

For very large projects, monitor memory usage:

- Watch mode keeps some state in memory
- Template cache grows over time
- Restart watch mode periodically if needed

## Best practices

### 1. Project organisation

Keep source and output separate:

```
project/
├── docs/
│   ├── pages/          # Source files
│   ├── templates/      # Custom templates  
│   └── output/         # Generated files
├── src/                # Your code
└── pyproject.toml
```

### 2. Template development

When creating templates:

1. Start with a simple template
2. Use watch mode for rapid iteration
3. Test with multiple modules/classes
4. Validate syntax regularly

### 3. File organisation

Organise source files logically:

```
docs/pages/
├── api/
│   ├── core.md         # Core module docs
│   ├── utils.md        # Utilities docs
│   └── database.md     # Database docs
└── guides/
    ├── installation.md
    └── tutorial.md
```

### 4. Error handling

Handle errors gracefully:

- Fix template errors immediately
- Check module import paths
- Validate frontmatter syntax
- Use `griffonner validate` for templates

### 5. Performance

Optimise for large projects:

- Keep source files focused (one module per file)
- Use efficient templates
- Restart watch mode if it becomes slow
- Consider splitting very large projects

## Advanced usage

### Custom file patterns

While watch mode only monitors `.md` and `.markdown` files, you can use symbolic links or file organisation to include other patterns.

### Integration with build systems

Watch mode can be integrated with other tools:

**Make:**
```makefile
.PHONY: docs-watch
docs-watch:
    griffonner watch docs/pages/ --output docs/output

.PHONY: docs-build  
docs-build:
    griffonner generate docs/pages/ --output docs/output
```

**Just:**
```justfile
# Watch mode for development
docs-watch:
    griffonner watch docs/pages/ --output docs/output

# One-time generation
docs-build:
    griffonner generate docs/pages/ --output docs/output
```

### CI/CD considerations

For CI/CD pipelines:

- Use `griffonner generate` for builds (not watch mode)
- Watch mode is for development only
- Consider caching generated documentation

## Next steps

- Learn about [template development](templates.md)
- Check the [CLI reference](cli-reference.md) for all options
- Explore [template customisation](template-reference.md)