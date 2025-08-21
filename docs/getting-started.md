# Getting started

This guide walks you through creating your first documentation with Griffonner.

## Installation

Install Griffonner using pip:

```shell
pip install griffonner
```

## Your first documentation

Let's create documentation for Python's built-in `pathlib` module to demonstrate Griffonner's capabilities.

### Step 1: Create a project structure

```shell
mkdir my-docs
cd my-docs
mkdir -p docs/pages docs/output
```

### Step 2: Create your first page

Create `docs/pages/pathlib-guide.md`:

```markdown
---
template: "python/default/module.md.jinja2"
output:
  - filename: "pathlib-reference.md"
    griffe_target: "pathlib"
custom_vars:
  title: "Pathlib module reference"
  description: "Modern object-oriented filesystem paths"
---

# Pathlib guide

This page demonstrates Griffonner by documenting Python's `pathlib` module.

The content below will be automatically generated from the Python source code.
```

### Step 3: Generate documentation

```shell
griffonner generate docs/pages/pathlib-guide.md --output docs/output
```

This creates `docs/output/pathlib-reference.md` with automatically generated documentation for the `pathlib` module.

### Step 4: View the results

The generated file includes:

- Module overview and description
- Class documentation with inheritance
- Method signatures and parameters  
- Comprehensive API reference

## Next steps

### Use watch mode for development

For live editing, use watch mode:

```shell
griffonner watch docs/pages/ --output docs/output
```

Now when you modify `docs/pages/pathlib-guide.md`, the output will automatically regenerate.

### Explore built-in templates

See what templates are available:

```shell
griffonner templates
```

Try different templates by changing the `template` field in your frontmatter.

### Document your own code

Replace `"pathlib"` with your own Python module:

```markdown
---
template: "python/default/module.md.jinja2"
output:
  - filename: "my-module-docs.md"
    griffe_target: "mypackage.mymodule"
---
```

### Customise with variables

Add custom variables to personalise your documentation:

```markdown
---
template: "python/default/module.md.jinja2"
output:
  - filename: "api-reference.md"
    griffe_target: "myapp.database"
custom_vars:
  project_name: "My Application"
  version: "1.0.0"
  emoji: "🗄️"
---
```

## Common patterns

### Multiple outputs from one source

Generate multiple formats from a single source file:

```markdown
---
template: "python/default/module.md.jinja2"
output:
  - filename: "api-brief.md"
    griffe_target: "myapp.core"
    griffe_options:
      include_private: false
  - filename: "api-detailed.md" 
    griffe_target: "myapp.core"
    griffe_options:
      include_private: true
      show_source: true
---
```

### Directory-based organisation

Organise your source files to match your output structure:

```
docs/
├── pages/
│   ├── api/
│   │   ├── core.md
│   │   ├── utils.md
│   │   └── database.md
│   └── guides/
│       └── overview.md
└── output/
    ├── api/
    │   ├── core.md
    │   ├── utils.md
    │   └── database.md
    └── guides/
        └── overview.md
```

Generate everything at once:

```shell
griffonner generate docs/pages/ --output docs/output
```

## Troubleshooting

### Template not found

If you get a "template not found" error, check:

1. Template path is correct in frontmatter
2. Template exists in search directories
3. File has `.jinja2` extension

Use `griffonner templates` to list available templates.

### Invalid frontmatter

Ensure your YAML frontmatter is valid:

- Starts and ends with `---`
- Proper YAML syntax
- Required fields present (`template`, `output`)

### Module import errors

If Griffe can't import your module:

- Ensure the module is installed or in PYTHONPATH
- Check module path spelling
- Verify the module can be imported normally

## What's next?

- Learn about [template development](templates.md)
- Explore the [CLI reference](cli-reference.md)
- Set up [watch mode](watch-mode.md) for development