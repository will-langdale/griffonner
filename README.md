# Griffonner

Template-first Python documentation generator that gets out of your way.

> *From French "griffonner" (to scribble/draft) - because [Griffe](https://mkdocstrings.github.io/griffe/) finds it, you sketch it out*

## Quick start

1. Create a markdown file with frontmatter:

```markdown
---
template: "python/default/module.md.jinja2"
griffe_target: "mypackage.utils"
output:
  filename: "api-utils.md"
---

# Optional content here
```

2. Generate documentation:

```shell
pip install griffonner
griffonner generate docs/pages/
```

That's it! Griffonner uses [Griffe](https://mkdocstrings.github.io/griffe/) to parse your Python code and Jinja2 templates to generate docs in any format you want.

## Features

- **Zero opinions** - You control output format through templates
- **Frontmatter-driven** - Configuration in your markdown files
- **Template ecosystem** - Share and reuse templates
- **Format agnostic** - Generate Markdown, RST, HTML, JSON, anything

## Example templates

```shell
# List available templates
griffonner templates

# Generate with custom template
---
template: "python/gitlab-wiki/module.md.jinja2"
griffe_target: "myapp.database"
custom_vars:
  emoji: "🗄️"
  category: "Core"
---
```

## CLI

```shell
griffonner generate docs/pages/           # Generate all
griffonner generate docs/pages/api.md    # Generate one
griffonner watch docs/pages/             # Watch mode
```

## Contributing

We use [uv](https://github.com/astral-sh/uv) for dependency management and [just](https://github.com/casey/just) for task running:

```shell
git clone https://github.com/yourusername/griffonner
cd griffonner
uv sync
just test    # Run tests
just format  # Lint and format code
just -l      # See other tasks
```
