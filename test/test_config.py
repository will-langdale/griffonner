"""Tests for configuration loading and management."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from griffonner.config import (
    GriffonnerConfig,
    TemplatesConfig,
    _deep_merge,
    find_config_file,
    load_config,
    merge_config_with_args,
    merge_griffe_config,
)


class TestTemplatesConfig:
    """Test TemplatesConfig model."""

    def test_default_pattern(self):
        """Test default pattern value."""
        config = TemplatesConfig()
        assert config.pattern == "**/*.jinja2"

    def test_custom_pattern(self):
        """Test custom pattern value."""
        config = TemplatesConfig(pattern="*.md.jinja2")
        assert config.pattern == "*.md.jinja2"


class TestGriffonnerConfig:
    """Test GriffonnerConfig model."""

    def test_default_values(self):
        """Test all default configuration values."""
        config = GriffonnerConfig()

        assert config.output_dir == Path("docs/output")
        assert config.template_dirs == []
        assert config.local_plugins == []
        assert config.ignore == []
        assert config.verbose is False
        assert config.griffe == {}
        assert isinstance(config.templates, TemplatesConfig)
        assert config.templates.pattern == "**/*.jinja2"

    def test_custom_values(self):
        """Test custom configuration values."""
        config = GriffonnerConfig(
            output_dir=Path("build/docs"),
            template_dirs=[Path("templates"), Path("custom")],
            local_plugins=["myproject.plugins"],
            ignore=["*.tmp", "*.log"],
            verbose=True,
            griffe={"loader": {"allow_inspection": False}},
            templates=TemplatesConfig(pattern="*.html.jinja2"),
        )

        assert config.output_dir == Path("build/docs")
        assert config.template_dirs == [Path("templates"), Path("custom")]
        assert config.local_plugins == ["myproject.plugins"]
        assert config.ignore == ["*.tmp", "*.log"]
        assert config.verbose is True
        assert config.griffe == {"loader": {"allow_inspection": False}}
        assert config.templates.pattern == "*.html.jinja2"


class TestDeepMerge:
    """Test deep merge functionality."""

    def test_simple_merge(self):
        """Test simple dictionary merge."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = _deep_merge(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_merge(self):
        """Test nested dictionary merge."""
        base = {"a": {"x": 1, "y": 2}, "b": 3}
        override = {"a": {"y": 4, "z": 5}, "c": 6}
        result = _deep_merge(base, override)

        assert result == {"a": {"x": 1, "y": 4, "z": 5}, "b": 3, "c": 6}

    def test_deep_nested_merge(self):
        """Test deeply nested dictionary merge."""
        base = {"loader": {"load": {"submodules": True}, "allow_inspection": True}}
        override = {
            "loader": {"load": {"find_stubs_package": False}, "store_source": False}
        }
        result = _deep_merge(base, override)

        expected = {
            "loader": {
                "load": {"submodules": True, "find_stubs_package": False},
                "allow_inspection": True,
                "store_source": False,
            }
        }
        assert result == expected

    def test_override_with_non_dict(self):
        """Test override with non-dictionary values."""
        base = {"a": {"x": 1, "y": 2}}
        override = {"a": "string_value"}
        result = _deep_merge(base, override)

        assert result == {"a": "string_value"}


class TestConfigFileLoading:
    """Test configuration file loading."""

    def test_yaml_config_loading(self):
        """Test loading YAML configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "griffonner.yml"
            config_data = {
                "output_dir": "build/docs",
                "template_dirs": ["templates"],
                "local_plugins": ["myproject.plugins"],
                "ignore": ["*.tmp"],
                "verbose": True,
                "griffe": {"loader": {"allow_inspection": False, "store_source": True}},
                "templates": {"pattern": "*.md.jinja2"},
            }

            with open(config_file, "w") as f:
                yaml.safe_dump(config_data, f)

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()

            assert config.output_dir == Path("build/docs")
            assert config.template_dirs == [Path("templates")]
            assert config.local_plugins == ["myproject.plugins"]
            assert config.ignore == ["*.tmp"]
            assert config.verbose is True
            expected_griffe = {
                "loader": {"allow_inspection": False, "store_source": True}
            }
            assert config.griffe == expected_griffe
            assert config.templates.pattern == "*.md.jinja2"

    @pytest.mark.parametrize("filename", ["griffonner.yml", "griffonner.yaml"])
    def test_yaml_file_discovery(self, filename):
        """Test YAML config file discovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / filename
            config_file.write_text("verbose: true")

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                found = find_config_file()

            assert found == config_file

    def test_toml_config_loading(self):
        """Test loading TOML configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "pyproject.toml"
            toml_content = """
[tool.griffonner]
output_dir = "build/docs"
template_dirs = ["templates"]
local_plugins = ["myproject.plugins"]
ignore = ["*.tmp"]
verbose = true

[tool.griffonner.griffe.loader]
allow_inspection = false
store_source = true

[tool.griffonner.templates]
pattern = "*.md.jinja2"
"""
            config_file.write_text(toml_content)

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()

            assert config.output_dir == Path("build/docs")
            assert config.template_dirs == [Path("templates")]
            assert config.local_plugins == ["myproject.plugins"]
            assert config.ignore == ["*.tmp"]
            assert config.verbose is True
            expected_griffe = {
                "loader": {"allow_inspection": False, "store_source": True}
            }
            assert config.griffe == expected_griffe
            assert config.templates.pattern == "*.md.jinja2"

    def test_empty_config_file(self):
        """Test loading empty configuration file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "griffonner.yml"
            config_file.write_text("")

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()

            # Should return defaults
            assert config.output_dir == Path("docs/output")
            assert config.verbose is False

    def test_no_config_file(self):
        """Test loading when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()

            # Should return defaults
            assert config.output_dir == Path("docs/output")
            assert config.verbose is False

    def test_invalid_yaml_config(self):
        """Test loading invalid YAML configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "griffonner.yml"
            config_file.write_text("invalid: yaml: content:")

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                with pytest.raises(ValueError, match="Invalid YAML"):
                    load_config()

    def test_config_file_priority(self):
        """Test configuration file discovery priority."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple config files
            yml_file = Path(tmpdir) / "griffonner.yml"
            yaml_file = Path(tmpdir) / "griffonner.yaml"
            toml_file = Path(tmpdir) / "pyproject.toml"

            yml_file.write_text("verbose: true")
            yaml_file.write_text("verbose: false")
            toml_file.write_text("[tool.griffonner]\nverbose = false")

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                found = find_config_file()

            # Should find .yml first
            assert found == yml_file

    def test_toml_without_griffonner_section(self):
        """Test TOML file without [tool.griffonner] section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "pyproject.toml"
            config_file.write_text("[build-system]\nrequires = ['setuptools']")

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                found = find_config_file()

            # Should not find this file
            assert found is None


class TestConfigMerging:
    """Test configuration merging with CLI arguments."""

    def test_merge_with_cli_args(self):
        """Test merging configuration with CLI arguments."""
        base_config = GriffonnerConfig(
            output_dir=Path("docs/output"),
            template_dirs=[Path("templates")],
            verbose=False,
        )

        merged = merge_config_with_args(
            base_config,
            output_dir=Path("build/docs"),
            template_dirs=[Path("custom")],
            verbose=True,
        )

        assert merged.output_dir == Path("build/docs")
        assert merged.template_dirs == [Path("custom")]
        assert merged.verbose is True

    def test_merge_with_partial_cli_args(self):
        """Test merging with partial CLI arguments."""
        base_config = GriffonnerConfig(
            output_dir=Path("docs/output"),
            template_dirs=[Path("templates")],
            verbose=False,
        )

        merged = merge_config_with_args(base_config, verbose=True)

        # CLI arg should override
        assert merged.verbose is True
        # Config values should remain
        assert merged.output_dir == Path("docs/output")
        assert merged.template_dirs == [Path("templates")]

    def test_merge_with_none_cli_args(self):
        """Test merging with None CLI arguments."""
        base_config = GriffonnerConfig(output_dir=Path("docs/output"), verbose=False)

        merged = merge_config_with_args(base_config, output_dir=None, verbose=None)

        # Should keep original values
        assert merged.output_dir == Path("docs/output")
        assert merged.verbose is False


class TestGriffeConfigMerging:
    """Test Griffe configuration merging."""

    def test_griffe_config_merge(self):
        """Test merging Griffe configurations."""
        default_config = {
            "loader": {
                "allow_inspection": True,
                "store_source": True,
                "load": {"submodules": True},
            }
        }

        frontmatter_config = {
            "loader": {
                "allow_inspection": False,
                "load": {"find_stubs_package": False},
                "resolve_aliases": {"external": True},
            }
        }

        result = merge_griffe_config(default_config, frontmatter_config)

        expected = {
            "loader": {
                "allow_inspection": False,  # Overridden
                "store_source": True,  # From default
                "load": {
                    "submodules": True,  # From default
                    "find_stubs_package": False,  # From frontmatter
                },
                "resolve_aliases": {
                    "external": True  # From frontmatter
                },
            }
        }

        assert result == expected

    def test_empty_griffe_configs(self):
        """Test merging empty Griffe configurations."""
        result = merge_griffe_config({}, {})
        assert result == {}

    def test_griffe_config_with_empty_default(self):
        """Test merging with empty default Griffe config."""
        frontmatter_config = {"loader": {"allow_inspection": False}}
        result = merge_griffe_config({}, frontmatter_config)
        assert result == frontmatter_config

    def test_griffe_config_with_empty_frontmatter(self):
        """Test merging with empty frontmatter Griffe config."""
        default_config = {"loader": {"allow_inspection": True}}
        result = merge_griffe_config(default_config, {})
        assert result == default_config


class TestConfigValidation:
    """Test configuration validation."""

    def test_invalid_config_data(self):
        """Test invalid configuration data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "griffonner.yml"
            # Invalid data - verbose should be bool, not string
            config_file.write_text("verbose: 'not_a_bool'")

            with patch("griffonner.config.Path.cwd", return_value=Path(tmpdir)):
                with pytest.raises(ValueError, match="Invalid configuration"):
                    load_config()

    def test_explicit_config_path_loading(self):
        """Test loading configuration from explicit path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "custom_config.yml"
            config_file.write_text("verbose: true")

            config = load_config(config_file)
            assert config.verbose is True

    def test_explicit_nonexistent_config_path(self):
        """Test loading configuration from nonexistent explicit path."""
        nonexistent_path = Path("/nonexistent/config.yml")
        config = load_config(nonexistent_path)

        # Should return defaults
        assert config.verbose is False

    def test_unsupported_config_file_format(self):
        """Test loading unsupported configuration file format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "config.json"
            config_file.write_text('{"verbose": true}')

            with pytest.raises(ValueError, match="Unsupported config file format"):
                load_config(config_file)
