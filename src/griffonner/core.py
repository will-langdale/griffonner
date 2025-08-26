"""Main generation logic for Griffonner."""

import logging
import textwrap
from pathlib import Path
from typing import List, Optional

from .frontmatter import find_frontmatter_files, parse_frontmatter_file
from .griffe_wrapper import load_griffe_object
from .plugins.manager import PluginManager
from .templates import TemplateLoader

logger = logging.getLogger("griffonner.core")


class GenerationError(Exception):
    """Base exception for generation errors."""


def generate_file(
    source_file: Path,
    output_dir: Path,
    template_dirs: Optional[List[Path]] = None,
    plugin_manager: Optional[PluginManager] = None,
) -> List[Path]:
    """Generate documentation files from a source file with frontmatter.

    Args:
        source_file: Path to source file with frontmatter
        output_dir: Base output directory
        template_dirs: Additional template search directories
        plugin_manager: Optional plugin manager for processors/filters

    Returns:
        List of generated output file paths

    Raises:
        GenerationError: If generation fails
    """
    logger.info(f"Generating documentation from: {source_file}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Template directories: {template_dirs}")

    # Parse the frontmatter file
    logger.info("Parsing frontmatter file")
    parsed = parse_frontmatter_file(source_file)
    logger.info(f"Template: {parsed.frontmatter.template}")
    logger.info(f"Output items: {len(parsed.frontmatter.output)}")

    # Calculate output directory (preserve structure from pages/ to output/)
    relative_dir = source_file.parent.name if source_file.parent.name != "." else ""
    target_output_dir = output_dir / relative_dir if relative_dir else output_dir
    logger.info(f"Target output directory: {target_output_dir}")
    target_output_dir.mkdir(parents=True, exist_ok=True)

    # Initialise plugin manager if not provided
    if plugin_manager is None:
        logger.info("Creating new PluginManager instance")
        plugin_manager = PluginManager()
    else:
        logger.info("Using provided PluginManager instance")

    # Initialise template loader with plugin filters
    logger.info("Initialising TemplateLoader")
    template_loader = TemplateLoader(template_dirs, plugin_manager)

    generated_files = []

    # Generate each output
    logger.info(f"Processing {len(parsed.frontmatter.output)} output items")
    for i, output_item in enumerate(parsed.frontmatter.output):
        logger.info(f"Processing output item {i+1}: {output_item.filename}")
        logger.info(f"Griffe target: {output_item.griffe_target}")

        try:
            # Load Griffe object for this output
            logger.info(f"Loading Griffe object for: {output_item.griffe_target}")
            griffe_obj = load_griffe_object(
                output_item.griffe_target,
                griffe_config=parsed.frontmatter.griffe,
            )

            # Prepare initial template context
            logger.info("Preparing template context")
            context = {
                "obj": griffe_obj,
                "custom_vars": parsed.frontmatter.custom_vars,
                "source_content": parsed.content,
                "source_path": source_file,
                "processor_config": (
                    parsed.frontmatter.processors.config
                    if parsed.frontmatter.processors
                    else {}
                ),
            }
            logger.info(f"Context keys prepared: {list(context.keys())}")

            # Determine which processors to use
            processor_names = None
            if parsed.frontmatter.processors:
                if parsed.frontmatter.processors.enabled:
                    # Use only explicitly enabled processors
                    processor_names = parsed.frontmatter.processors.enabled
                    logger.info(f"Using enabled processors: {processor_names}")
                elif parsed.frontmatter.processors.disabled:
                    # Use all processors except disabled ones
                    all_processors = list(plugin_manager.get_processors().keys())
                    processor_names = [
                        p
                        for p in all_processors
                        if p not in parsed.frontmatter.processors.disabled
                    ]
                    disabled_processors = parsed.frontmatter.processors.disabled
                    logger.info(f"Using all processors except: {disabled_processors}")
                    logger.info(f"Effective processors: {processor_names}")
            else:
                logger.info("No processor configuration, using all available")

            # Run processors on Griffe object and context
            logger.info("Running processors on Griffe object and context")
            processed_obj, processed_context = plugin_manager.process_griffe_object(
                griffe_obj, context, processor_names
            )

            # Update context with processed object
            processed_context["obj"] = processed_obj
            logger.info("Updated context with processed object")

            # Render template
            logger.info(f"Rendering template: {parsed.frontmatter.template}")
            rendered_content = template_loader.render_template(
                parsed.frontmatter.template, processed_context
            )

            # Write output file
            output_file = target_output_dir / output_item.filename
            logger.info(f"Writing output file: {output_file}")
            output_file.write_text(rendered_content, encoding="utf-8")
            generated_files.append(output_file)
            logger.info(f"Successfully generated: {output_file}")

        except Exception as e:
            logger.exception(f"Failed to generate {output_item.filename}")
            raise GenerationError(
                f"Failed to generate {output_item.filename} from {source_file}: {e}"
            ) from e

    logger.info(f"File generation completed: {len(generated_files)} files generated")
    return generated_files


def generate_directory(
    pages_dir: Path,
    output_dir: Path,
    template_dirs: Optional[List[Path]] = None,
    plugin_manager: Optional[PluginManager] = None,
) -> List[Path]:
    """Generate documentation from all files in a directory.

    Args:
        pages_dir: Directory containing source files with frontmatter
        output_dir: Base output directory
        template_dirs: Additional template search directories
        plugin_manager: Optional plugin manager for processors/filters

    Returns:
        List of all generated output file paths

    Raises:
        GenerationError: If generation fails
    """
    logger.info(f"Generating documentation from directory: {pages_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Find all frontmatter files
    logger.info("Searching for frontmatter files")
    source_files = find_frontmatter_files(pages_dir)
    logger.info(f"Found {len(source_files)} frontmatter files")

    if not source_files:
        logger.error(f"No frontmatter files found in {pages_dir}")
        error_msg = textwrap.dedent(f"""\
            No frontmatter files found in {pages_dir}

            Looking for files that start with:
            ---
            template: "python/default/module.md.jinja2"
            output:
              filename: "api.md"
              griffe_target: "mypackage.module"
            ---""")
        raise GenerationError(error_msg)

    all_generated = []
    errors = []

    # Generate each file, collecting errors
    logger.info(f"Processing {len(source_files)} source files")
    for i, source_file in enumerate(source_files):
        logger.info(f"Processing file {i+1}/{len(source_files)}: {source_file}")
        try:
            generated = generate_file(
                source_file, output_dir, template_dirs, plugin_manager
            )
            all_generated.extend(generated)
            logger.info(f"Processed {source_file}: {len(generated)} files generated")
        except Exception as e:
            logger.exception(f"Failed to process {source_file}")
            errors.append(f"Failed to generate {source_file}: {e}")

    # If there were errors, include summary
    if errors:
        logger.error(f"Directory generation completed with {len(errors)} errors")
        error_parts = [f"Generation completed with {len(errors)} errors:"]
        error_parts.extend(f"  - {err}" for err in errors)
        error_msg = "\n".join(error_parts)
        raise GenerationError(error_msg)

    generated_count = len(all_generated)
    logger.info(f"Directory generation completed: {generated_count} total files")
    return all_generated


def generate(
    source: Path,
    output_dir: Path,
    template_dirs: Optional[List[Path]] = None,
    plugin_manager: Optional[PluginManager] = None,
) -> List[Path]:
    """Generate documentation from a file or directory.

    Args:
        source: Source file or directory path
        output_dir: Output directory path
        template_dirs: Additional template search directories
        plugin_manager: Optional plugin manager for processors/filters

    Returns:
        List of generated output file paths

    Raises:
        GenerationError: If generation fails
    """
    logger.info(f"Starting generation from source: {source}")
    logger.info(f"Output directory: {output_dir}")

    if not source.exists():
        logger.error(f"Source not found: {source}")
        raise GenerationError(f"Source not found: {source}")

    if source.is_file():
        logger.info("Source is a file, using generate_file")
        return generate_file(source, output_dir, template_dirs, plugin_manager)
    elif source.is_dir():
        logger.info("Source is a directory, using generate_directory")
        return generate_directory(source, output_dir, template_dirs, plugin_manager)
    else:
        logger.error(f"Source is neither file nor directory: {source}")
        raise GenerationError(f"Source must be a file or directory: {source}")
