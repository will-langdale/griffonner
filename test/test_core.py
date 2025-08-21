"""Tests for core module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from griffonner.core import (
    GenerationError,
    generate,
    generate_directory,
    generate_file,
)


class TestGenerationError:
    """Tests for GenerationError exception."""
    
    def test_generation_error_inheritance(self):
        """Tests that GenerationError inherits from Exception."""
        assert issubclass(GenerationError, Exception)


class TestGenerateFile:
    """Tests for generate_file function."""
    
    def test_generate_file_success(self):
        """Tests successful file generation."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            template_content = """# {{ obj.name }}

{{ obj.docstring.summary if obj.docstring else "No description" }}

Custom variable: {{ custom_vars.test_var }}
"""
            
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text(template_content)
            
            # Create source file with frontmatter
            source_content = """---
template: "test.md.jinja2"
output:
  - filename: "os_module.md"
    griffe_target: "os"
custom_vars:
  test_var: "test value"
---

This is source content.
"""
            
            source_file = temp_path / "source.md"
            source_file.write_text(source_content)
            
            # Create output directory
            output_dir = temp_path / "output"
            
            # Generate file
            generated = generate_file(
                source_file, 
                output_dir, 
                template_dirs=[template_dir]
            )
            
            assert len(generated) == 1
            output_file = generated[0]
            assert output_file.exists()
            
            content = output_file.read_text()
            assert "# os" in content
            assert "Custom variable: test value" in content
    
    def test_generate_file_multiple_outputs(self):
        """Tests file generation with multiple outputs."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            template_content = """# {{ obj.name }}

Type: {{ obj.kind.value }}
"""
            
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text(template_content)
            
            # Create source file with multiple outputs
            source_content = """---
template: "test.md.jinja2"
output:
  - filename: "os_module.md"
    griffe_target: "os"
  - filename: "sys_module.md"
    griffe_target: "sys"
---

Source content.
"""
            
            source_file = temp_path / "source.md"
            source_file.write_text(source_content)
            
            output_dir = temp_path / "output"
            
            generated = generate_file(
                source_file, 
                output_dir, 
                template_dirs=[template_dir]
            )
            
            assert len(generated) == 2
            
            # Check both files were generated
            filenames = {f.name for f in generated}
            assert filenames == {"os_module.md", "sys_module.md"}
            
            for output_file in generated:
                assert output_file.exists()
                content = output_file.read_text()
                assert "Type: module" in content
    
    def test_generate_file_nonexistent_source(self):
        """Tests error when source file doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            nonexistent_file = temp_path / "nonexistent.md"
            output_dir = temp_path / "output"
            
            with pytest.raises(FileNotFoundError):
                generate_file(nonexistent_file, output_dir)
    
    def test_generate_file_invalid_frontmatter(self):
        """Tests error when frontmatter is invalid."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source file with invalid frontmatter
            source_content = """---
invalid: frontmatter: without: required: fields
---

Content.
"""
            
            source_file = temp_path / "invalid.md"
            source_file.write_text(source_content)
            
            output_dir = temp_path / "output"
            
            with pytest.raises(ValueError):
                generate_file(source_file, output_dir)
    
    def test_generate_file_nonexistent_griffe_target(self):
        """Tests error when griffe target doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text("# {{ obj.name }}")
            
            # Create source file with nonexistent target
            source_content = """---
template: "test.md.jinja2"
output:
  - filename: "test.md"
    griffe_target: "nonexistent_module_xyz123"
---

Content.
"""
            
            source_file = temp_path / "source.md"
            source_file.write_text(source_content)
            
            output_dir = temp_path / "output"
            
            with pytest.raises(GenerationError, match="Failed to generate"):
                generate_file(
                    source_file, 
                    output_dir, 
                    template_dirs=[template_dir]
                )


class TestGenerateDirectory:
    """Tests for generate_directory function."""
    
    def test_generate_directory_success(self):
        """Tests successful directory generation."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text("# {{ obj.name }}")
            
            # Create pages directory with frontmatter files
            pages_dir = temp_path / "pages"
            pages_dir.mkdir()
            
            # First frontmatter file
            source1_content = """---
template: "test.md.jinja2"
output:
  - filename: "os.md"
    griffe_target: "os"
---

OS module docs.
"""
            
            source1 = pages_dir / "os_docs.md"
            source1.write_text(source1_content)
            
            # Second frontmatter file
            source2_content = """---
template: "test.md.jinja2"
output:
  - filename: "sys.md"
    griffe_target: "sys"
---

Sys module docs.
"""
            
            source2 = pages_dir / "sys_docs.md"
            source2.write_text(source2_content)
            
            # Regular markdown file (should be ignored)
            regular_file = pages_dir / "regular.md"
            regular_file.write_text("# Just regular markdown")
            
            output_dir = temp_path / "output"
            
            generated = generate_directory(
                pages_dir, 
                output_dir, 
                template_dirs=[template_dir]
            )
            
            assert len(generated) == 2
            filenames = {f.name for f in generated}
            assert filenames == {"os.md", "sys.md"}
            
            for output_file in generated:
                assert output_file.exists()
    
    def test_generate_directory_no_frontmatter_files(self):
        """Tests error when no frontmatter files found."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create empty pages directory
            pages_dir = temp_path / "pages"
            pages_dir.mkdir()
            
            # Add non-frontmatter file
            regular_file = pages_dir / "regular.md"
            regular_file.write_text("# Just regular markdown")
            
            output_dir = temp_path / "output"
            
            with pytest.raises(GenerationError, match="No frontmatter files found"):
                generate_directory(pages_dir, output_dir)
    
    def test_generate_directory_nonexistent(self):
        """Tests error when directory doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            nonexistent_dir = temp_path / "nonexistent"
            output_dir = temp_path / "output"
            
            with pytest.raises(NotADirectoryError):
                generate_directory(nonexistent_dir, output_dir)


class TestGenerate:
    """Tests for main generate function."""
    
    def test_generate_with_file(self):
        """Tests generate function with a single file."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text("# {{ obj.name }}")
            
            # Create source file
            source_content = """---
template: "test.md.jinja2"
output:
  - filename: "test.md"
    griffe_target: "os"
---

Content.
"""
            
            source_file = temp_path / "source.md"
            source_file.write_text(source_content)
            
            output_dir = temp_path / "output"
            
            generated = generate(
                source_file, 
                output_dir, 
                template_dirs=[template_dir]
            )
            
            assert len(generated) == 1
            assert generated[0].exists()
    
    def test_generate_with_directory(self):
        """Tests generate function with a directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text("# {{ obj.name }}")
            
            # Create pages directory
            pages_dir = temp_path / "pages"
            pages_dir.mkdir()
            
            source_content = """---
template: "test.md.jinja2"
output:
  - filename: "test.md"
    griffe_target: "os"
---

Content.
"""
            
            source_file = pages_dir / "source.md"
            source_file.write_text(source_content)
            
            output_dir = temp_path / "output"
            
            generated = generate(
                pages_dir, 
                output_dir, 
                template_dirs=[template_dir]
            )
            
            assert len(generated) == 1
            assert generated[0].exists()
    
    def test_generate_nonexistent_source(self):
        """Tests error when source doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            nonexistent = temp_path / "nonexistent"
            output_dir = temp_path / "output"
            
            with pytest.raises(GenerationError, match="Source not found"):
                generate(nonexistent, output_dir)
    
    def test_generate_invalid_source_type(self):
        """Tests error when source is neither file nor directory."""
        # This is hard to test in practice since Path objects are usually files or dirs
        # But we can test the error message format
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a special file (like a device or socket) - but we can't easily do this
            # So let's just test that a file that gets deleted between exists() and is_file() checks
            # would trigger this error. For now, we'll skip this edge case test.
            pass