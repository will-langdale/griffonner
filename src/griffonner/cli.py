"""Typer-based CLI for Griffonner."""

from pathlib import Path
from typing import Annotated, List, Optional

import typer

from .core import generate
from .templates import TemplateLoader, TemplateValidationError
from .watcher import DocumentationWatcher

app = typer.Typer(
    name="griffonner",
    help="Template-first Python documentation generator",
    no_args_is_help=True,
)


@app.command("generate")
def generate_cmd(
    source: Annotated[
        Path, typer.Argument(help="Source file or directory with frontmatter")
    ],
    output_dir: Annotated[
        Path, typer.Option("--output", "-o", help="Output directory")
    ] = Path("docs/output"),
    template_dirs: Annotated[
        Optional[List[Path]],
        typer.Option("--template-dir", "-t", help="Additional template directories"),
    ] = None,
) -> None:
    """Generate documentation from source files with frontmatter."""
    template_dirs = template_dirs or []

    try:
        generated_files = generate(source, output_dir, template_dirs)

        typer.echo(f"✅ Generated {len(generated_files)} files:")
        for file_path in generated_files:
            typer.echo(f"  {file_path}")

    except Exception as e:
        typer.echo(f"❌ Generation failed: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def templates(
    template_dirs: Annotated[
        Optional[List[Path]],
        typer.Option("--template-dir", "-t", help="Template directories to search"),
    ] = None,
    pattern: Annotated[
        str, typer.Option("--pattern", "-p", help="Pattern to match templates")
    ] = "**/*.jinja2",
) -> None:
    """List available templates."""
    template_dirs = template_dirs or []

    try:
        loader = TemplateLoader(template_dirs)
        found_templates = loader.find_templates(pattern)

        if not found_templates:
            typer.echo("No templates found")
            return

        typer.echo(f"📋 Found {len(found_templates)} templates:")
        for template_path in found_templates:
            typer.echo(f"  {template_path}")

    except Exception as e:
        typer.echo(f"❌ Failed to list templates: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def validate(
    template_path: Annotated[str, typer.Argument(help="Template path to validate")],
    template_dirs: Annotated[
        Optional[List[Path]],
        typer.Option("--template-dir", "-t", help="Template directories to search"),
    ] = None,
) -> None:
    """Validate template syntax and structure."""
    template_dirs = template_dirs or []

    try:
        loader = TemplateLoader(template_dirs)
        loader.validate_template(template_path)
        typer.echo(f"✅ Template is valid: {template_path}")

    except TemplateValidationError as e:
        typer.echo(f"❌ Template validation failed: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"❌ Validation error: {e}", err=True)
        raise typer.Exit(1) from e


@app.command()
def watch(
    source: Annotated[Path, typer.Argument(help="Source directory to watch")],
    output_dir: Annotated[
        Path, typer.Option("--output", "-o", help="Output directory")
    ] = Path("docs/output"),
    template_dirs: Annotated[
        Optional[List[Path]],
        typer.Option("--template-dir", "-t", help="Additional template directories"),
    ] = None,
) -> None:
    """Watch source directory for changes and regenerate documentation."""
    template_dirs = template_dirs or []

    try:
        watcher = DocumentationWatcher(source, output_dir, template_dirs)
        watcher.watch()
    except KeyboardInterrupt:
        # Already handled by the watcher
        pass
    except Exception as e:
        typer.echo(f"❌ Watch failed: {e}", err=True)
        raise typer.Exit(1) from e


def main() -> None:
    """Main entry point for the CLI."""
    app()
