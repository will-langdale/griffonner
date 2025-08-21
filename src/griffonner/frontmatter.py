"""YAML frontmatter parsing for Griffonner."""

import re
from pathlib import Path
from typing import Any, Dict, List

import yaml
from pydantic import BaseModel, Field, field_validator


class GriffeOptions(BaseModel):
    """Options for Griffe parsing."""

    include_private: bool = False
    show_source: bool = True
    docstring_style: str = "google"
    include_inherited: bool = False
    load_plugins: bool = True


class OutputItem(BaseModel):
    """Single output configuration."""

    filename: str
    griffe_target: str


class FrontmatterConfig(BaseModel):
    """Configuration parsed from frontmatter."""

    template: str
    output: List[OutputItem]
    griffe_options: GriffeOptions = Field(default_factory=GriffeOptions)
    custom_vars: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        """Validate template path format."""
        if not v.endswith((".jinja2", ".j2")):
            raise ValueError("Template must end with .jinja2 or .j2")
        return v


class ParsedFile(BaseModel):
    """A parsed file with frontmatter and content."""

    frontmatter: FrontmatterConfig
    content: str
    source_path: Path


def parse_frontmatter_file(file_path: Path) -> ParsedFile:
    """Parse a file with YAML frontmatter.

    Args:
        file_path: Path to the file to parse

    Returns:
        ParsedFile with frontmatter config and content

    Raises:
        ValueError: If frontmatter is invalid or missing
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8")

    # Match frontmatter pattern
    pattern = r"^---\s*\n(.*?)\n---\s*\n?(.*)"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        raise ValueError(f"No valid frontmatter found in {file_path}")

    frontmatter_yaml, body_content = match.groups()

    try:
        frontmatter_data = yaml.safe_load(frontmatter_yaml)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

    if not isinstance(frontmatter_data, dict):
        raise ValueError("Frontmatter must be a YAML mapping")

    try:
        frontmatter_config = FrontmatterConfig.model_validate(frontmatter_data)
    except Exception as e:
        raise ValueError(f"Invalid frontmatter configuration: {e}") from e

    return ParsedFile(
        frontmatter=frontmatter_config,
        content=body_content.strip(),
        source_path=file_path,
    )


def find_frontmatter_files(directory: Path) -> List[Path]:
    """Find all files with frontmatter in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of paths to files with frontmatter

    Raises:
        NotADirectoryError: If directory doesn't exist or isn't a directory
    """
    if not directory.exists():
        raise NotADirectoryError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    frontmatter_files = []

    for file_path in directory.rglob("*.md"):
        try:
            content = file_path.read_text(encoding="utf-8")
            if content.startswith("---\n"):
                frontmatter_files.append(file_path)
        except (UnicodeDecodeError, PermissionError):
            # Skip files we can't read
            continue

    return sorted(frontmatter_files)
