"""Typer-based CLI for Griffonner."""

import logging
from pathlib import Path
from typing import Annotated, List, Optional

import typer

from .core import generate
from .plugins.manager import PluginManager
from .templates import TemplateLoader, TemplateValidationError
from .watcher import DocumentationWatcher

logger = logging.getLogger("griffonner.cli")


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Enable verbose logging if True
    """
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
    )


app = typer.Typer(
    name="griffonner",
    help="Template-first Python documentation generator",
    no_args_is_help=True,
)


@app.callback()
def main_callback(
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Enable verbose output")
    ] = False,
) -> None:
    """Main callback to handle global options."""
    if verbose:
        setup_logging(verbose=True)


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

    logger.info(f"Beginning generation: source={source}, output={output_dir}")
    logger.info(f"Template directories: {template_dirs}")

    try:
        generated_files = generate(source, output_dir, template_dirs)

        typer.echo(f"✅ Generated {len(generated_files)} files:")
        for file_path in generated_files:
            typer.echo(f"  {file_path}")

    except Exception as e:
        logger.exception("Generation failed with exception")
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

    logger.info(f"Searching for templates with pattern: {pattern}")
    logger.info(f"Template directories: {template_dirs}")

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
        logger.exception("Template discovery failed with exception")
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

    logger.info(f"Validating template: {template_path}")
    logger.info(f"Template directories: {template_dirs}")

    try:
        loader = TemplateLoader(template_dirs)
        loader.validate_template(template_path)
        typer.echo(f"✅ Template is valid: {template_path}")

    except TemplateValidationError as e:
        logger.exception("Template validation failed with exception")
        typer.echo(f"❌ Template validation failed: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        logger.exception("Template validation error")
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

    logger.info(f"Starting watch mode: source={source}, output={output_dir}")
    logger.info(f"Template directories: {template_dirs}")

    try:
        watcher = DocumentationWatcher(source, output_dir, template_dirs)
        watcher.watch()
    except KeyboardInterrupt:
        logger.info("Watch mode interrupted by user")
        pass
    except Exception as e:
        logger.exception("Watch mode failed with exception")
        typer.echo(f"❌ Watch failed: {e}", err=True)
        raise typer.Exit(1) from e


@app.command("plugins")
def plugins_cmd() -> None:
    """List all available plugins (processors, filters, bundles)."""
    logger.info("Discovering available plugins")

    try:
        plugin_manager = PluginManager()
        plugins = plugin_manager.list_plugins()

        if not any(plugins.values()):
            typer.echo("No plugins found")
            return

        typer.echo("🔌 Available plugins:")

        if plugins["processors"]:
            typer.echo("\n📋 Processors:")
            for processor in plugins["processors"]:
                typer.echo(f"  - {processor}")
            logger.info(f"Found {len(plugins['processors'])} processors")

        if plugins["filters"]:
            typer.echo("\n🔧 Filters:")
            for filter_name in plugins["filters"]:
                typer.echo(f"  - {filter_name}")
            logger.info(f"Found {len(plugins['filters'])} filters")

        if plugins["bundles"]:
            typer.echo("\n📦 Bundles:")
            for bundle in plugins["bundles"]:
                typer.echo(f"  - {bundle}")
            logger.info(f"Found {len(plugins['bundles'])} bundles")

    except Exception as e:
        logger.exception("Plugin discovery failed with exception")
        typer.echo(f"❌ Failed to list plugins: {e}", err=True)
        raise typer.Exit(1) from e


@app.command("bundle")
def bundle_info_cmd(
    bundle_name: Annotated[str, typer.Argument(help="Bundle name to inspect")],
) -> None:
    """Show detailed information about a specific bundle."""
    logger.info(f"Getting information for bundle: {bundle_name}")

    try:
        plugin_manager = PluginManager()
        bundle_info = plugin_manager.get_bundle_info(bundle_name)

        if not bundle_info:
            typer.echo(f"❌ Bundle not found: {bundle_name}")
            logger.info(f"Bundle not found: {bundle_name}")
            raise typer.Exit(1)

        typer.echo(f"📦 Bundle: {bundle_info['name']}")
        typer.echo(f"   Version: {bundle_info['version']}")
        typer.echo(f"   Description: {bundle_info['description']}")

        if bundle_info["processors"]:
            typer.echo("\n   📋 Processors:")
            for processor in bundle_info["processors"]:
                typer.echo(f"     - {processor}")

        if bundle_info["filters"]:
            typer.echo("\n   🔧 Filters:")
            for filter_name in bundle_info["filters"]:
                typer.echo(f"     - {filter_name}")

        if bundle_info["template_paths"]:
            typer.echo("\n   📄 Template paths:")
            for template_path in bundle_info["template_paths"]:
                typer.echo(f"     - {template_path}")

    except Exception as e:
        logger.exception("Bundle info retrieval failed with exception")
        typer.echo(f"❌ Failed to get bundle info: {e}", err=True)
        raise typer.Exit(1) from e


def main() -> None:
    """Main entry point for the CLI."""
    app()
