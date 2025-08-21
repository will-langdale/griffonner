"""Main generation logic for Griffonner."""

from pathlib import Path
from typing import List, Optional

from .frontmatter import find_frontmatter_files, parse_frontmatter_file
from .griffe_wrapper import load_griffe_object
from .templates import TemplateLoader


class GenerationError(Exception):
    """Base exception for generation errors."""


def generate_file(
    source_file: Path, output_dir: Path, template_dirs: Optional[List[Path]] = None
) -> List[Path]:
    """Generate documentation files from a source file with frontmatter.

    Args:
        source_file: Path to source file with frontmatter
        output_dir: Base output directory
        template_dirs: Additional template search directories

    Returns:
        List of generated output file paths

    Raises:
        GenerationError: If generation fails
    """
    # Parse the frontmatter file
    parsed = parse_frontmatter_file(source_file)

    # Calculate output directory (preserve structure from pages/ to output/)
    relative_dir = source_file.parent.name if source_file.parent.name != "." else ""
    target_output_dir = output_dir / relative_dir if relative_dir else output_dir
    target_output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize template loader
    template_loader = TemplateLoader(template_dirs)

    generated_files = []

    # Generate each output
    for output_item in parsed.frontmatter.output:
        try:
            # Load Griffe object for this output
            griffe_obj = load_griffe_object(output_item.griffe_target)

            # Prepare template context
            context = {
                "obj": griffe_obj,
                "custom_vars": parsed.frontmatter.custom_vars,
                "source_content": parsed.content,
                "source_path": source_file,
            }

            # Render template
            rendered_content = template_loader.render_template(
                parsed.frontmatter.template, context
            )

            # Write output file
            output_file = target_output_dir / output_item.filename
            output_file.write_text(rendered_content, encoding="utf-8")
            generated_files.append(output_file)

        except Exception as e:
            raise GenerationError(
                f"Failed to generate {output_item.filename} from {source_file}: {e}"
            ) from e

    return generated_files


def generate_directory(
    pages_dir: Path, output_dir: Path, template_dirs: Optional[List[Path]] = None
) -> List[Path]:
    """Generate documentation from all files in a directory.

    Args:
        pages_dir: Directory containing source files with frontmatter
        output_dir: Base output directory
        template_dirs: Additional template search directories

    Returns:
        List of all generated output file paths

    Raises:
        GenerationError: If generation fails
    """
    # Find all frontmatter files
    source_files = find_frontmatter_files(pages_dir)

    if not source_files:
        raise GenerationError(f"No frontmatter files found in {pages_dir}")

    all_generated = []

    # Generate each file
    for source_file in source_files:
        generated = generate_file(source_file, output_dir, template_dirs)
        all_generated.extend(generated)

    return all_generated


def generate(
    source: Path, output_dir: Path, template_dirs: Optional[List[Path]] = None
) -> List[Path]:
    """Generate documentation from a file or directory.

    Args:
        source: Source file or directory path
        output_dir: Output directory path
        template_dirs: Additional template search directories

    Returns:
        List of generated output file paths

    Raises:
        GenerationError: If generation fails
    """
    if not source.exists():
        raise GenerationError(f"Source not found: {source}")

    if source.is_file():
        return generate_file(source, output_dir, template_dirs)
    elif source.is_dir():
        return generate_directory(source, output_dir, template_dirs)
    else:
        raise GenerationError(f"Source must be a file or directory: {source}")
