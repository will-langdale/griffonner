"""Main generation logic for Griffonner."""

import fnmatch
import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .config import merge_griffe_config
from .frontmatter import parse_frontmatter_file
from .griffe_wrapper import load_griffe_object
from .plugins.manager import PluginManager
from .templates import TemplateLoader

logger = logging.getLogger("griffonner.core")


class GenerationError(Exception):
    """Base exception for generation errors."""


def find_all_files(
    directory: Path, ignore_patterns: Optional[List[str]] = None
) -> List[Path]:
    """Find all files in a directory recursively, excluding ignored patterns.

    Args:
        directory: Directory to search
        ignore_patterns: Glob patterns to ignore

    Returns:
        List of all file paths not matching ignore patterns

    Raises:
        NotADirectoryError: If directory doesn't exist or isn't a directory
    """
    ignore_patterns = ignore_patterns or []
    logger.info(f"Finding all files in: {directory}")
    logger.info(f"Ignore patterns: {ignore_patterns}")

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        raise NotADirectoryError(f"Directory not found: {directory}")

    if not directory.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    all_files = []
    skipped_files = []
    ignored_files = []

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        # Check if file matches any ignore patterns
        try:
            relative_path = file_path.relative_to(directory)
            # Normalise path for consistent matching across platforms
            relative_str = str(relative_path).replace("\\", "/")

            # Check if file matches any ignore pattern
            is_ignored = any(
                fnmatch.fnmatch(relative_str, pattern) for pattern in ignore_patterns
            )

            if is_ignored:
                ignored_files.append(file_path)
                logger.info(f"Ignored file (matches pattern): {file_path}")
                continue
        except ValueError:
            # File is not within directory (shouldn't happen with rglob)
            continue

        try:
            # Quick check that file is readable
            file_path.read_text(encoding="utf-8", errors="strict")
            all_files.append(file_path)
            logger.info(f"Found file: {file_path}")
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            logger.warning(f"Skipping unreadable file {file_path}: {e}")
            skipped_files.append(file_path)
            continue

    logger.info(
        f"Found {len(all_files)} files, {len(skipped_files)} skipped, "
        f"{len(ignored_files)} ignored"
    )
    return sorted(all_files)


def categorise_files(files: List[Path]) -> Tuple[List[Path], List[Path]]:
    """Categorise files into frontmatter files and passthrough files.

    Args:
        files: List of file paths to categorise

    Returns:
        Tuple of (frontmatter_files, passthrough_files)
    """
    logger.info(f"Categorising {len(files)} files")

    frontmatter_files = []
    passthrough_files = []

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
            if content.startswith("---\n"):
                frontmatter_files.append(file_path)
                logger.info(f"Frontmatter file: {file_path}")
            else:
                passthrough_files.append(file_path)
                logger.info(f"Passthrough file: {file_path}")
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            logger.warning(f"Error reading {file_path}, treating as passthrough: {e}")
            passthrough_files.append(file_path)

    logger.info(
        f"Categorised: {len(frontmatter_files)} frontmatter, "
        f"{len(passthrough_files)} passthrough"
    )
    return frontmatter_files, passthrough_files


def copy_file_passthrough(
    source_file: Path, source_dir: Path, output_dir: Path
) -> Path:
    """Copy a file from source to output preserving directory structure.

    Args:
        source_file: Source file path
        source_dir: Base source directory
        output_dir: Base output directory

    Returns:
        Path to the copied output file

    Raises:
        GenerationError: If copy fails
    """
    logger.info(f"Copying passthrough file: {source_file}")

    # Calculate relative path from source_dir to source_file
    try:
        relative_path = source_file.relative_to(source_dir)
    except ValueError as e:
        raise GenerationError(
            f"Source file {source_file} is not within source directory {source_dir}"
        ) from e

    # Calculate target output file path
    output_file = output_dir / relative_path
    logger.info(f"Target output path: {output_file}")

    # Create parent directories if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Copy the file
        shutil.copy2(source_file, output_file)
        logger.info(f"Successfully copied: {source_file} -> {output_file}")
        return output_file
    except (OSError, IOError) as e:
        logger.exception(f"Failed to copy {source_file} to {output_file}")
        raise GenerationError(
            f"Failed to copy {source_file} to {output_file}: {e}"
        ) from e


def generate_file(
    source_file: Path,
    source_dir: Path,
    output_dir: Path,
    template_dirs: Optional[List[Path]] = None,
    plugin_manager: Optional[PluginManager] = None,
    default_griffe_config: Optional[Dict[str, Any]] = None,
) -> List[Path]:
    """Generate documentation files from a source file with frontmatter.

    Args:
        source_file: Path to source file with frontmatter
        source_dir: Base source directory for calculating relative paths
        output_dir: Base output directory
        template_dirs: Additional template search directories
        plugin_manager: Optional plugin manager for processors/filters
        default_griffe_config: Default Griffe configuration to merge with frontmatter

    Returns:
        List of generated output file paths

    Raises:
        GenerationError: If generation fails
    """
    logger.info(f"Generating documentation from: {source_file}")
    logger.info(f"Source directory: {source_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Template directories: {template_dirs}")

    # Parse the frontmatter file
    logger.info("Parsing frontmatter file")
    parsed = parse_frontmatter_file(source_file)
    logger.info(f"Template: {parsed.frontmatter.template}")
    logger.info(f"Output items: {len(parsed.frontmatter.output)}")

    # Calculate output directory (preserve structure from source_dir to output/)
    # Check if the source file's parent is within the source directory.
    if source_dir == source_file.parent or source_dir in source_file.parent.parents:
        relative_dir = source_file.parent.relative_to(source_dir)
    else:
        # If not, output to the root of the output directory. This typically
        # happens when a single file is passed as the source.
        relative_dir = Path()

    target_output_dir = output_dir / relative_dir
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
            # Merge default Griffe config with frontmatter config
            default_config = default_griffe_config or {}
            merged_griffe_config = merge_griffe_config(
                default_config, parsed.frontmatter.griffe
            )
            logger.info(f"Merged Griffe config: {merged_griffe_config}")

            # Load Griffe object for this output
            logger.info(f"Loading Griffe object for: {output_item.griffe_target}")
            griffe_obj = load_griffe_object(
                output_item.griffe_target,
                griffe_config=merged_griffe_config,
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
                **parsed.frontmatter.custom_vars,
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
    ignore_patterns: Optional[List[str]] = None,
    default_griffe_config: Optional[Dict[str, Any]] = None,
) -> List[Path]:
    """Generate documentation from all files in a directory.

    Args:
        pages_dir: Directory containing source files (with or without frontmatter)
        output_dir: Base output directory
        template_dirs: Additional template search directories
        plugin_manager: Optional plugin manager for processors/filters
        ignore_patterns: Glob patterns to ignore
        default_griffe_config: Default Griffe configuration to merge with frontmatter

    Returns:
        List of all generated and copied output file paths

    Raises:
        GenerationError: If generation fails
    """
    logger.info(f"Generating documentation from directory: {pages_dir}")
    logger.info(f"Output directory: {output_dir}")

    # Find all files
    logger.info("Searching for all files")
    all_files = find_all_files(pages_dir, ignore_patterns)
    logger.info(f"Found {len(all_files)} total files")

    if not all_files:
        logger.warning(f"No files found in {pages_dir}")
        return []

    # Categorise files into frontmatter and passthrough
    logger.info("Categorising files")
    frontmatter_files, passthrough_files = categorise_files(all_files)
    logger.info(
        f"Files: {len(frontmatter_files)} frontmatter, "
        f"{len(passthrough_files)} passthrough"
    )

    all_output_files = []
    errors = []

    # Process frontmatter files (generate using templates)
    if frontmatter_files:
        logger.info(f"Processing {len(frontmatter_files)} frontmatter files")
        for i, source_file in enumerate(frontmatter_files):
            logger.info(
                f"Processing frontmatter file {i+1}/{len(frontmatter_files)}: "
                f"{source_file}"
            )
            try:
                generated = generate_file(
                    source_file,
                    pages_dir,
                    output_dir,
                    template_dirs,
                    plugin_manager,
                    default_griffe_config,
                )
                all_output_files.extend(generated)
                logger.info(f"Generated {len(generated)} files from {source_file}")
            except Exception as e:
                logger.exception(f"Failed to process frontmatter file {source_file}")
                errors.append(f"Failed to generate {source_file}: {e}")

    # Process passthrough files (copy directly)
    if passthrough_files:
        logger.info(f"Processing {len(passthrough_files)} passthrough files")
        for i, source_file in enumerate(passthrough_files):
            logger.info(
                f"Processing passthrough file {i+1}/{len(passthrough_files)}: "
                f"{source_file}"
            )
            try:
                copied_file = copy_file_passthrough(source_file, pages_dir, output_dir)
                all_output_files.append(copied_file)
                logger.info(f"Copied passthrough file: {source_file} -> {copied_file}")
            except Exception as e:
                logger.exception(f"Failed to copy passthrough file {source_file}")
                errors.append(f"Failed to copy {source_file}: {e}")

    # If there were errors, include summary
    if errors:
        logger.error(f"Directory processing completed with {len(errors)} errors")
        error_parts = [f"Processing completed with {len(errors)} errors:"]
        error_parts.extend(f"  - {err}" for err in errors)
        error_msg = "\n".join(error_parts)
        raise GenerationError(error_msg)

    output_count = len(all_output_files)
    logger.info(f"Directory processing completed: {output_count} total output files")
    generated_count = len(
        [
            f
            for f in all_output_files
            if any(str(f).endswith(ext) for ext in [".md", ".html", ".rst"])
        ]
    )
    logger.info(f"  - Generated: {generated_count}")
    logger.info(f"  - Copied: {len(passthrough_files)}")
    return all_output_files


def generate(
    source: Path,
    output_dir: Path,
    template_dirs: Optional[List[Path]] = None,
    plugin_manager: Optional[PluginManager] = None,
    ignore_patterns: Optional[List[str]] = None,
    default_griffe_config: Optional[Dict[str, Any]] = None,
) -> List[Path]:
    """Generate documentation from a file or directory.

    Args:
        source: Source file or directory path
        output_dir: Output directory path
        template_dirs: Additional template search directories
        plugin_manager: Optional plugin manager for processors/filters
        ignore_patterns: Glob patterns to ignore
        default_griffe_config: Default Griffe configuration to merge with frontmatter

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
        # Use the parent directory of the file as the source_dir
        return generate_file(
            source,
            source.parent,
            output_dir,
            template_dirs,
            plugin_manager,
            default_griffe_config,
        )
    elif source.is_dir():
        logger.info("Source is a directory, using generate_directory")
        return generate_directory(
            source,
            output_dir,
            template_dirs,
            plugin_manager,
            ignore_patterns,
            default_griffe_config,
        )
    else:
        logger.error(f"Source is neither file nor directory: {source}")
        raise GenerationError(f"Source must be a file or directory: {source}")
