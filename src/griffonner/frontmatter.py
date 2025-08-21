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
        error_msg = f"No valid frontmatter found in {file_path}"
        if content.strip():
            if content.startswith("---"):
                error_msg += "\n\nThe file starts with '---' but the frontmatter "
                error_msg += "format is invalid."
                error_msg += "\n\nExpected format:\n"
                error_msg += "---\n"
                error_msg += 'template: "python/default/module.md.jinja2"\n'
                error_msg += "output:\n"
                error_msg += '  filename: "api.md"\n'
                error_msg += '  griffe_target: "mypackage.module"\n'
                error_msg += "---\n"
            else:
                error_msg += "\n\nThe file should start with YAML frontmatter "
                error_msg += "enclosed in '---' delimiters."
        else:
            error_msg += "\n\nThe file is empty. Please add frontmatter and content."
        raise ValueError(error_msg)

    frontmatter_yaml, body_content = match.groups()

    try:
        frontmatter_data = yaml.safe_load(frontmatter_yaml)
    except yaml.YAMLError as e:
        error_msg = f"Invalid YAML in frontmatter: {e}"
        error_msg += f"\n\nIn file: {file_path}"
        error_msg += "\n\nPlease check the YAML syntax in your frontmatter section."
        raise ValueError(error_msg) from e

    if not isinstance(frontmatter_data, dict):
        error_msg = "Frontmatter must be a YAML mapping (key-value pairs)"
        error_msg += f"\n\nIn file: {file_path}"
        error_msg += "\n\nFound type: " + type(frontmatter_data).__name__
        raise ValueError(error_msg)

    try:
        frontmatter_config = FrontmatterConfig.model_validate(frontmatter_data)
    except Exception as e:
        error_msg = f"Invalid frontmatter configuration: {e}"
        error_msg += f"\n\nIn file: {file_path}"
        error_msg += "\n\nRequired fields:"
        error_msg += "\n  - template: Template path "
        error_msg += "(e.g., 'python/default/module.md.jinja2')"
        error_msg += "\n  - output: List with filename and griffe_target"
        raise ValueError(error_msg) from e

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
