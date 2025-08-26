"""YAML frontmatter parsing for Griffonner."""

import logging
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("griffonner.frontmatter")


class OutputItem(BaseModel):
    """Single output configuration."""

    filename: str
    griffe_target: str


class ProcessorConfig(BaseModel):
    """Configuration for processors."""

    enabled: List[str] = Field(default_factory=list)
    disabled: List[str] = Field(default_factory=list)
    config: Dict[str, Any] = Field(default_factory=dict)


class FrontmatterConfig(BaseModel):
    """Configuration parsed from frontmatter."""

    template: str
    output: List[OutputItem]
    griffe: Dict[str, Any] = Field(default_factory=dict)
    custom_vars: Dict[str, Any] = Field(default_factory=dict)
    processors: Optional[ProcessorConfig] = Field(default=None)

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
    logger.info(f"Parsing frontmatter file: {file_path}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    logger.info(f"Reading file content: {file_path}")
    content = file_path.read_text(encoding="utf-8")
    logger.info(f"File size: {len(content)} characters")

    # Match frontmatter pattern
    pattern = r"^---\s*\n(.*?)\n---\s*\n?(.*)"
    logger.info("Matching frontmatter pattern")
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        logger.error(f"No valid frontmatter pattern found in {file_path}")
        base_msg = f"No valid frontmatter found in {file_path}"

        if content.strip():
            if content.startswith("---"):
                logger.info("File starts with '---' but format is invalid")
                error_msg = textwrap.dedent(f"""\
                    {base_msg}

                    The file starts with '---' but the frontmatter format is invalid.

                    Expected format:
                    ---
                    template: "python/default/module.md.jinja2"
                    output:
                      filename: "api.md"
                      griffe_target: "mypackage.module"
                    ---""")
            else:
                logger.info("File does not start with '---'")
                error_msg = textwrap.dedent(f"""\
                    {base_msg}

                    The file should start with YAML frontmatter enclosed in '---' 
                    delimiters.""")
        else:
            logger.info("File is empty")
            error_msg = textwrap.dedent(f"""\
                {base_msg}

                The file is empty. Please add frontmatter and content.""")
        raise ValueError(error_msg)

    frontmatter_yaml, body_content = match.groups()
    yaml_len, content_len = len(frontmatter_yaml), len(body_content)
    logger.info(f"Extracted YAML ({yaml_len} chars) and body ({content_len} chars)")

    try:
        logger.info("Parsing YAML frontmatter")
        frontmatter_data = yaml.safe_load(frontmatter_yaml)
        data_type = type(frontmatter_data).__name__
        logger.info(f"YAML parsed successfully, type: {data_type}")
        if isinstance(frontmatter_data, dict):
            logger.info(f"YAML keys: {list(frontmatter_data.keys())}")
    except yaml.YAMLError as e:
        logger.exception(f"YAML parsing failed for {file_path}")
        error_msg = textwrap.dedent(f"""\
            Invalid YAML in frontmatter: {e}

            In file: {file_path}

            Please check the YAML syntax in your frontmatter section.""")
        raise ValueError(error_msg) from e

    if not isinstance(frontmatter_data, dict):
        logger.error(f"Frontmatter is not a dict: {type(frontmatter_data).__name__}")
        error_msg = textwrap.dedent(f"""\
            Frontmatter must be a YAML mapping (key-value pairs)

            In file: {file_path}

            Found type: {type(frontmatter_data).__name__}""")
        raise ValueError(error_msg)

    try:
        logger.info("Validating frontmatter configuration with Pydantic")
        frontmatter_config = FrontmatterConfig.model_validate(frontmatter_data)
        logger.info("Frontmatter validation successful")
        logger.info(f"Template: {frontmatter_config.template}")
        logger.info(f"Output items: {len(frontmatter_config.output)}")
        if frontmatter_config.processors:
            logger.info("Processors config present")
        if frontmatter_config.custom_vars:
            logger.info(f"Custom vars: {list(frontmatter_config.custom_vars.keys())}")
    except Exception as e:
        logger.exception(f"Frontmatter validation failed for {file_path}")
        error_msg = textwrap.dedent(f"""\
            Invalid frontmatter configuration: {e}

            In file: {file_path}

            Required fields:
              - template: Template path (e.g., 'python/default/module.md.jinja2')
              - output: List with filename and griffe_target""")
        raise ValueError(error_msg) from e

    parsed_file = ParsedFile(
        frontmatter=frontmatter_config,
        content=body_content.strip(),
        source_path=file_path,
    )
    logger.info(f"Successfully parsed frontmatter file: {file_path}")
    return parsed_file


def find_frontmatter_files(directory: Path) -> List[Path]:
    """Find all files with frontmatter in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of paths to files with frontmatter

    Raises:
        NotADirectoryError: If directory doesn't exist or isn't a directory
    """
    logger.info(f"Searching for frontmatter files in: {directory}")

    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        raise NotADirectoryError(f"Directory not found: {directory}")

    if not directory.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        raise NotADirectoryError(f"Path is not a directory: {directory}")

    logger.info("Searching for all files recursively")
    frontmatter_files = []
    all_files = []
    skipped_files = []

    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue
        all_files.append(file_path)
        try:
            content = file_path.read_text(encoding="utf-8")
            if content.startswith("---\n"):
                frontmatter_files.append(file_path)
                logger.info(f"Found frontmatter file: {file_path}")
            else:
                logger.info(f"Markdown file without frontmatter: {file_path}")
        except (UnicodeDecodeError, PermissionError) as e:
            # Skip files we can't read
            logger.warning(f"Skipping unreadable file {file_path}: {e}")
            skipped_files.append(file_path)
            continue

    total_files_count = len(all_files)
    frontmatter_count = len(frontmatter_files)
    skipped_count = len(skipped_files)
    logger.info(
        f"Scan: {total_files_count} files, {frontmatter_count} with frontmatter, "
        f"{skipped_count} skipped"
    )
    return sorted(frontmatter_files)
