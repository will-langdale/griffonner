"""Tests for frontmatter module."""

import pytest
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

from griffonner.frontmatter import (
    FrontmatterConfig,
    GriffeOptions,
    OutputItem,
    ParsedFile,
    find_frontmatter_files,
    parse_frontmatter_file,
)


class TestGriffeOptions:
    """Tests for GriffeOptions model."""
    
    def test_default_values(self):
        """Tests default values are set correctly."""
        options = GriffeOptions()
        assert options.include_private is False
        assert options.show_source is True
        assert options.docstring_style == "google"
        assert options.include_inherited is False
        assert options.load_plugins is True


class TestOutputItem:
    """Tests for OutputItem model."""
    
    def test_valid_output_item(self):
        """Tests valid output item creation."""
        item = OutputItem(filename="test.md", griffe_target="mymodule")
        assert item.filename == "test.md"
        assert item.griffe_target == "mymodule"
    
    def test_missing_required_fields(self):
        """Tests that required fields raise validation errors."""
        with pytest.raises(ValueError):
            OutputItem()


class TestFrontmatterConfig:
    """Tests for FrontmatterConfig model."""
    
    def test_valid_config(self):
        """Tests valid frontmatter configuration."""
        config = FrontmatterConfig(
            template="python/default/module.md.jinja2",
            output=[OutputItem(filename="test.md", griffe_target="mymodule")]
        )
        assert config.template == "python/default/module.md.jinja2"
        assert len(config.output) == 1
        assert config.output[0].filename == "test.md"
    
    def test_template_validation(self):
        """Tests template path validation."""
        with pytest.raises(ValueError, match="Template must end with .jinja2 or .j2"):
            FrontmatterConfig(
                template="invalid_template.txt",
                output=[OutputItem(filename="test.md", griffe_target="mymodule")]
            )
    
    def test_j2_extension_valid(self):
        """Tests that .j2 extension is valid."""
        config = FrontmatterConfig(
            template="python/default/module.j2",
            output=[OutputItem(filename="test.md", griffe_target="mymodule")]
        )
        assert config.template == "python/default/module.j2"


class TestParseFrontmatterFile:
    """Tests for parse_frontmatter_file function."""
    
    def test_valid_frontmatter_file(self):
        """Tests parsing a valid frontmatter file."""
        content = """---
template: "python/default/module.md.jinja2"
output:
  - filename: "test.md"
    griffe_target: "mymodule"
custom_vars:
  emoji: "📚"
---

# This is content
Some markdown content here.
"""
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            
            parsed = parse_frontmatter_file(Path(f.name))
            
            assert parsed.frontmatter.template == "python/default/module.md.jinja2"
            assert len(parsed.frontmatter.output) == 1
            assert parsed.frontmatter.output[0].filename == "test.md"
            assert parsed.frontmatter.custom_vars["emoji"] == "📚"
            assert "This is content" in parsed.content
            assert parsed.source_path == Path(f.name)
            
            Path(f.name).unlink()  # Clean up
    
    def test_file_not_found(self):
        """Tests error when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            parse_frontmatter_file(Path("nonexistent.md"))
    
    def test_no_frontmatter(self):
        """Tests error when no frontmatter is found."""
        content = "# Just regular markdown\nNo frontmatter here."
        
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            
            with pytest.raises(ValueError, match="No valid frontmatter found"):
                parse_frontmatter_file(Path(f.name))
            
            Path(f.name).unlink()
    
    def test_invalid_yaml(self):
        """Tests error when YAML is invalid."""
        content = """---
template: "test.jinja2"
invalid: yaml: content: here
---

Content here.
"""
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            
            with pytest.raises(ValueError, match="Invalid YAML in frontmatter"):
                parse_frontmatter_file(Path(f.name))
            
            Path(f.name).unlink()
    
    def test_invalid_frontmatter_config(self):
        """Tests error when frontmatter config is invalid."""
        content = """---
template: "invalid_template.txt"
output:
  - filename: "test.md"
    griffe_target: "mymodule"
---

Content here.
"""
        with NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            
            with pytest.raises(ValueError, match="Invalid frontmatter configuration"):
                parse_frontmatter_file(Path(f.name))
            
            Path(f.name).unlink()


class TestFindFrontmatterFiles:
    """Tests for find_frontmatter_files function."""
    
    def test_find_files_in_directory(self):
        """Tests finding frontmatter files in a directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create files with frontmatter
            frontmatter_content = """---
template: "test.jinja2"
output:
  - filename: "test.md"
    griffe_target: "mymodule"
---

Content here.
"""
            
            # Create frontmatter file
            frontmatter_file = temp_path / "with_frontmatter.md"
            frontmatter_file.write_text(frontmatter_content)
            
            # Create regular markdown file
            regular_file = temp_path / "regular.md"
            regular_file.write_text("# Just markdown\nNo frontmatter.")
            
            # Create subdirectory with frontmatter file
            subdir = temp_path / "subdir"
            subdir.mkdir()
            sub_frontmatter = subdir / "sub_frontmatter.md"
            sub_frontmatter.write_text(frontmatter_content)
            
            found_files = find_frontmatter_files(temp_path)
            
            assert len(found_files) == 2
            assert frontmatter_file in found_files
            assert sub_frontmatter in found_files
            assert regular_file not in found_files
    
    def test_directory_not_found(self):
        """Tests error when directory doesn't exist."""
        with pytest.raises(NotADirectoryError):
            find_frontmatter_files(Path("nonexistent_directory"))
    
    def test_path_is_not_directory(self):
        """Tests error when path is not a directory."""
        with NamedTemporaryFile() as f:
            with pytest.raises(NotADirectoryError):
                find_frontmatter_files(Path(f.name))
    
    def test_empty_directory(self):
        """Tests empty result when no frontmatter files found."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create non-markdown file
            txt_file = temp_path / "test.txt"
            txt_file.write_text("Not a markdown file")
            
            found_files = find_frontmatter_files(temp_path)
            assert len(found_files) == 0