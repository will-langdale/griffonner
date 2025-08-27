"""Configuration loading and management for Griffonner."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import tomli as tomllib
import yaml
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("griffonner.config")


class TemplatesConfig(BaseModel):
    """Configuration for template discovery."""

    pattern: str = Field(
        default="**/*.jinja2", description="Pattern to match templates"
    )


class GriffonnerConfig(BaseModel):
    """Main configuration model for Griffonner."""

    output_dir: Path = Field(
        default=Path("docs/output"), description="Output directory"
    )
    template_dirs: List[Path] = Field(
        default_factory=list, description="Additional template directories"
    )
    local_plugins: List[str] = Field(
        default_factory=list, description="Python modules containing local plugins"
    )
    ignore: List[str] = Field(
        default_factory=list,
        description="Glob patterns to ignore in source directory",
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    griffe: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default Griffe configuration (completely permissive)",
    )
    templates: TemplatesConfig = Field(
        default_factory=TemplatesConfig, description="Template configuration"
    )

    model_config = ConfigDict(validate_assignment=True)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with override taking precedence.

    Args:
        base: Base dictionary to merge into
        override: Dictionary to merge from (takes precedence)

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _load_yaml_config(config_path: Path) -> Optional[Dict[str, Any]]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Configuration dict or None if file doesn't exist

    Raises:
        ValueError: If YAML is invalid
    """
    if not config_path.exists():
        return None

    logger.info(f"Loading configuration from {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        return config_data if config_data else {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}") from e


def _load_toml_config(config_path: Path) -> Optional[Dict[str, Any]]:
    """Load configuration from pyproject.toml [tool.griffonner] section.

    Args:
        config_path: Path to pyproject.toml file

    Returns:
        Configuration dict or None if file doesn't exist or no section found

    Raises:
        ValueError: If TOML is invalid
    """
    if not config_path.exists():
        return None

    logger.info(f"Loading configuration from {config_path}")

    try:
        with open(config_path, "rb") as f:
            toml_data = tomllib.load(f)

        griffonner_config = toml_data.get("tool", {}).get("griffonner", {})
        return griffonner_config if griffonner_config else None
    except tomllib.TOMLDecodeError as e:
        raise ValueError(f"Invalid TOML in {config_path}: {e}") from e


def find_config_file(start_dir: Optional[Path] = None) -> Optional[Path]:
    """Find the first available configuration file.

    Searches in this order:
    1. griffonner.yml
    2. griffonner.yaml
    3. pyproject.toml (if it has [tool.griffonner] section)

    Args:
        start_dir: Directory to start search from (defaults to current working dir)

    Returns:
        Path to config file or None if none found
    """
    if start_dir is None:
        start_dir = Path.cwd()

    # Try YAML configs first
    for yaml_name in ["griffonner.yml", "griffonner.yaml"]:
        yaml_path = start_dir / yaml_name
        if yaml_path.exists():
            logger.info(f"Found configuration file: {yaml_path}")
            return yaml_path

    # Try pyproject.toml
    toml_path = start_dir / "pyproject.toml"
    if toml_path.exists():
        try:
            config_data = _load_toml_config(toml_path)
            if config_data:
                logger.info(f"Found configuration in pyproject.toml: {toml_path}")
                return toml_path
        except ValueError as e:
            logger.warning(f"Could not load pyproject.toml: {e}")

    logger.info("No configuration file found")
    return None


def load_config(config_path: Optional[Path] = None) -> GriffonnerConfig:
    """Load Griffonner configuration from file.

    If no config path is provided, searches for config files in current directory.

    Args:
        config_path: Explicit path to config file

    Returns:
        Loaded configuration with defaults for missing values

    Raises:
        ValueError: If config file is invalid
    """
    if config_path is None:
        config_path = find_config_file()

    if config_path is None:
        logger.info("No configuration file found, using defaults")
        return GriffonnerConfig()

    # Load based on file extension
    if config_path.suffix in [".yml", ".yaml"]:
        config_data = _load_yaml_config(config_path)
    elif config_path.name == "pyproject.toml":
        config_data = _load_toml_config(config_path)
    else:
        raise ValueError(f"Unsupported config file format: {config_path}")

    if config_data is None:
        logger.info("Configuration file exists but is empty, using defaults")
        return GriffonnerConfig()

    # Convert path strings to Path objects
    if "output_dir" in config_data:
        config_data["output_dir"] = Path(config_data["output_dir"])

    if "template_dirs" in config_data:
        config_data["template_dirs"] = [Path(p) for p in config_data["template_dirs"]]

    try:
        config = GriffonnerConfig(**config_data)
        logger.info(f"Successfully loaded configuration from {config_path}")
        return config
    except Exception as e:
        raise ValueError(f"Invalid configuration in {config_path}: {e}") from e


def merge_config_with_args(
    config: GriffonnerConfig,
    output_dir: Optional[Path] = None,
    template_dirs: Optional[List[Path]] = None,
    local_plugins: Optional[List[str]] = None,
    ignore: Optional[List[str]] = None,
    verbose: Optional[bool] = None,
) -> GriffonnerConfig:
    """Merge configuration with CLI arguments, giving precedence to CLI args.

    Args:
        config: Base configuration from file
        output_dir: CLI output directory argument
        template_dirs: CLI template directories argument
        local_plugins: CLI local plugins argument
        ignore: CLI ignore patterns argument
        verbose: CLI verbose flag

    Returns:
        Merged configuration with CLI args taking precedence
    """
    # Create dict of non-None CLI args
    cli_overrides: Dict[str, Any] = {}

    if output_dir is not None:
        cli_overrides["output_dir"] = output_dir

    if template_dirs is not None:
        cli_overrides["template_dirs"] = template_dirs

    if local_plugins is not None:
        cli_overrides["local_plugins"] = local_plugins

    if ignore is not None:
        cli_overrides["ignore"] = ignore

    if verbose is not None:
        cli_overrides["verbose"] = verbose

    # Convert to dict, merge, and create new config
    config_dict = config.model_dump()
    merged_dict = _deep_merge(config_dict, cli_overrides)

    return GriffonnerConfig(**merged_dict)


def merge_griffe_config(
    default_griffe_config: Dict[str, Any], frontmatter_griffe_config: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge default Griffe config with frontmatter Griffe config.

    Args:
        default_griffe_config: Default Griffe configuration from config file
        frontmatter_griffe_config: Griffe configuration from frontmatter

    Returns:
        Merged Griffe configuration with frontmatter taking precedence
    """
    return _deep_merge(default_griffe_config, frontmatter_griffe_config)
