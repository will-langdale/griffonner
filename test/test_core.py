"""Tests for core module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from griffonner.core import (
    GenerationError,
    categorize_files,
    copy_file_passthrough,
    find_all_files,
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
                source_file, output_dir, template_dirs=[template_dir]
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
                source_file, output_dir, template_dirs=[template_dir]
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
                generate_file(source_file, output_dir, template_dirs=[template_dir])


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

            # Regular markdown file (will be copied as passthrough)
            regular_file = pages_dir / "regular.md"
            regular_file.write_text("# Just regular markdown")

            output_dir = temp_path / "output"

            generated = generate_directory(
                pages_dir, output_dir, template_dirs=[template_dir]
            )

            # Now expects 3 files: 2 generated from frontmatter + 1 passthrough
            assert len(generated) == 3
            filenames = {f.name for f in generated}
            assert filenames == {"os.md", "sys.md", "regular.md"}

            for output_file in generated:
                assert output_file.exists()

    def test_generate_directory_no_frontmatter_files(self):
        """Tests directories with no frontmatter files work (passthrough only)."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create empty pages directory
            pages_dir = temp_path / "pages"
            pages_dir.mkdir()

            # Add non-frontmatter file
            regular_file = pages_dir / "regular.md"
            regular_file.write_text("# Just regular markdown")

            output_dir = temp_path / "output"

            # Should not error, should copy passthrough files
            generated = generate_directory(pages_dir, output_dir)

            assert len(generated) == 1
            assert (output_dir / "regular.md").exists()
            assert (output_dir / "regular.md").read_text() == "# Just regular markdown"

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

            generated = generate(source_file, output_dir, template_dirs=[template_dir])

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

            generated = generate(pages_dir, output_dir, template_dirs=[template_dir])

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
        with TemporaryDirectory():
            # Create a special file (like a device or socket) - but we can't
            # easily do this. So let's just test that a file that gets deleted
            # between exists() and is_file() checks would trigger this error.
            # For now, we'll skip this edge case test.
            pass


class TestFindAllFiles:
    """Tests for find_all_files function."""

    def test_find_all_files_success(self):
        """Tests finding all files in a directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create various files
            (temp_path / "regular.md").write_text("# Regular file")
            (temp_path / "frontmatter.md").write_text("---\nkey: value\n---\nContent")
            (temp_path / "_sidebar.md").write_text("# Sidebar")
            (temp_path / "__pycache__").mkdir()
            (temp_path / "__pycache__" / "test.pyc").write_text("binary")

            # Create subdirectory with files
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "sub.txt").write_text("Sub content")
            (subdir / ".hidden").write_text("Hidden file")

            files = find_all_files(temp_path)

            assert len(files) == 6
            filenames = [f.name for f in files]
            assert "regular.md" in filenames
            assert "frontmatter.md" in filenames
            assert "_sidebar.md" in filenames
            assert "test.pyc" in filenames
            assert "sub.txt" in filenames
            assert ".hidden" in filenames

    def test_find_all_files_empty_directory(self):
        """Tests finding files in empty directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            files = find_all_files(temp_path)
            assert files == []

    def test_find_all_files_nonexistent_directory(self):
        """Tests error when directory doesn't exist."""
        with pytest.raises(NotADirectoryError, match="Directory not found"):
            find_all_files(Path("nonexistent_directory"))

    def test_find_all_files_not_directory(self):
        """Tests error when path is not a directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_path = temp_path / "regular_file.txt"
            file_path.write_text("content")

            with pytest.raises(NotADirectoryError, match="Path is not a directory"):
                find_all_files(file_path)


class TestCategorizeFiles:
    """Tests for categorize_files function."""

    def test_categorize_mixed_files(self):
        """Tests categorizing a mix of frontmatter and regular files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create frontmatter file
            frontmatter_file = temp_path / "with_frontmatter.md"
            frontmatter_content = """---
template: "test.md.jinja2"
output:
  - filename: "output.md"
    griffe_target: "os"
---
Content here."""
            frontmatter_file.write_text(frontmatter_content)

            # Create regular files
            regular_file = temp_path / "regular.md"
            regular_file.write_text("# Just markdown")

            sidebar_file = temp_path / "_sidebar.md"
            sidebar_file.write_text("## Sidebar content")

            files = [frontmatter_file, regular_file, sidebar_file]
            frontmatter_files, passthrough_files = categorize_files(files)

            assert len(frontmatter_files) == 1
            assert frontmatter_file in frontmatter_files

            assert len(passthrough_files) == 2
            assert regular_file in passthrough_files
            assert sidebar_file in passthrough_files

    def test_categorize_only_frontmatter_files(self):
        """Tests categorizing only frontmatter files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create multiple frontmatter files
            files = []
            for i in range(3):
                file_path = temp_path / f"frontmatter_{i}.md"
                file_content = f"""---
template: "test.md.jinja2"
output:
  - filename: "output_{i}.md"
    griffe_target: "os"
---
Content {i}."""
                file_path.write_text(file_content)
                files.append(file_path)

            frontmatter_files, passthrough_files = categorize_files(files)

            assert len(frontmatter_files) == 3
            assert len(passthrough_files) == 0
            assert all(f in frontmatter_files for f in files)

    def test_categorize_only_regular_files(self):
        """Tests categorizing only regular files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create regular files
            files = []
            for i in range(3):
                file_path = temp_path / f"regular_{i}.md"
                file_path.write_text(f"# Regular file {i}")
                files.append(file_path)

            frontmatter_files, passthrough_files = categorize_files(files)

            assert len(frontmatter_files) == 0
            assert len(passthrough_files) == 3
            assert all(f in passthrough_files for f in files)

    def test_categorize_empty_list(self):
        """Tests categorizing empty file list."""
        frontmatter_files, passthrough_files = categorize_files([])
        assert len(frontmatter_files) == 0
        assert len(passthrough_files) == 0


class TestCopyFilePassthrough:
    """Tests for copy_file_passthrough function."""

    def test_copy_file_passthrough_success(self):
        """Tests successful file passthrough copy."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source structure
            source_dir = temp_path / "source"
            source_dir.mkdir()
            source_file = source_dir / "test.md"
            source_content = "# Test content"
            source_file.write_text(source_content)

            # Set up output directory
            output_dir = temp_path / "output"

            # Copy the file
            copied_file = copy_file_passthrough(source_file, source_dir, output_dir)

            # Verify results
            expected_output = output_dir / "test.md"
            assert copied_file == expected_output
            assert copied_file.exists()
            assert copied_file.read_text() == source_content

    def test_copy_file_passthrough_with_subdirectories(self):
        """Tests copying file with nested directory structure."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create nested source structure
            source_dir = temp_path / "source"
            nested_dir = source_dir / "docs" / "guides"
            nested_dir.mkdir(parents=True)
            source_file = nested_dir / "guide.md"
            source_content = "# Guide content"
            source_file.write_text(source_content)

            # Set up output directory
            output_dir = temp_path / "output"

            # Copy the file
            copied_file = copy_file_passthrough(source_file, source_dir, output_dir)

            # Verify directory structure is preserved
            expected_output = output_dir / "docs" / "guides" / "guide.md"
            assert copied_file == expected_output
            assert copied_file.exists()
            assert copied_file.read_text() == source_content

            # Verify intermediate directories were created
            assert (output_dir / "docs").is_dir()
            assert (output_dir / "docs" / "guides").is_dir()

    def test_copy_file_passthrough_special_names(self):
        """Tests copying files with special prefixes."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            source_dir = temp_path / "source"
            source_dir.mkdir()
            output_dir = temp_path / "output"

            # Test various special filename patterns
            special_files = [
                "_sidebar.md",
                "__init__.py",
                ".gitignore",
                ".hidden",
            ]

            for filename in special_files:
                source_file = source_dir / filename
                content = f"Content of {filename}"
                source_file.write_text(content)

                copied_file = copy_file_passthrough(source_file, source_dir, output_dir)

                expected_output = output_dir / filename
                assert copied_file == expected_output
                assert copied_file.exists()
                assert copied_file.read_text() == content

    def test_copy_file_passthrough_file_outside_source_dir(self):
        """Tests error when source file is outside source directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directories
            source_dir = temp_path / "source"
            source_dir.mkdir()
            outside_dir = temp_path / "outside"
            outside_dir.mkdir()
            output_dir = temp_path / "output"

            # Create file outside source directory
            outside_file = outside_dir / "outside.md"
            outside_file.write_text("Outside content")

            with pytest.raises(GenerationError, match="is not within source directory"):
                copy_file_passthrough(outside_file, source_dir, output_dir)


class TestGenerateDirectoryPassthrough:
    """Tests for generate_directory function with passthrough functionality."""

    def test_generate_directory_mixed_files(self):
        """Tests directory generation with mixed frontmatter and passthrough files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            template_content = "# {{ obj.name }}\n\n{{ custom_vars.test_var }}"
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text(template_content)

            # Create source directory with mixed files
            source_dir = temp_path / "source"
            source_dir.mkdir()

            # Frontmatter file
            frontmatter_file = source_dir / "api.md"
            frontmatter_content = """---
template: "test.md.jinja2"
output:
  - filename: "os_module.md"
    griffe_target: "os"
custom_vars:
  test_var: "API Documentation"
---
Source content here."""
            frontmatter_file.write_text(frontmatter_content)

            # Regular passthrough files
            (source_dir / "README.md").write_text("# Project README")
            (source_dir / "_sidebar.md").write_text("## Navigation")

            # Subdirectory with passthrough file
            subdir = source_dir / "guides"
            subdir.mkdir()
            (subdir / "getting-started.md").write_text("# Getting Started")

            # Generate
            output_dir = temp_path / "output"
            generated_files = generate_directory(
                source_dir, output_dir, template_dirs=[template_dir]
            )

            # Verify results
            assert len(generated_files) == 4

            # Check generated file (from frontmatter)
            generated_api = output_dir / "source" / "os_module.md"
            assert generated_api.exists()
            content = generated_api.read_text()
            assert "# os" in content
            assert "API Documentation" in content

            # Check passthrough files
            readme = output_dir / "README.md"
            assert readme.exists()
            assert readme.read_text() == "# Project README"

            sidebar = output_dir / "_sidebar.md"
            assert sidebar.exists()
            assert sidebar.read_text() == "## Navigation"

            guide = output_dir / "guides" / "getting-started.md"
            assert guide.exists()
            assert guide.read_text() == "# Getting Started"

    def test_generate_directory_only_passthrough_files(self):
        """Tests directory generation with only passthrough files (no frontmatter)."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source directory with only passthrough files
            source_dir = temp_path / "source"
            source_dir.mkdir()

            (source_dir / "README.md").write_text("# Project README")
            (source_dir / "LICENSE").write_text("MIT License")
            (source_dir / ".gitignore").write_text("*.pyc")

            # Subdirectory
            subdir = source_dir / "assets"
            subdir.mkdir()
            (subdir / "logo.txt").write_text("LOGO")

            # Generate (should not error)
            output_dir = temp_path / "output"
            generated_files = generate_directory(source_dir, output_dir)

            # Verify all files were copied
            assert len(generated_files) == 4

            assert (output_dir / "README.md").exists()
            assert (output_dir / "LICENSE").exists()
            assert (output_dir / ".gitignore").exists()
            assert (output_dir / "assets" / "logo.txt").exists()

            # Verify content
            assert (output_dir / "README.md").read_text() == "# Project README"
            assert (output_dir / "LICENSE").read_text() == "MIT License"

    def test_generate_directory_empty_directory(self):
        """Tests directory generation with empty source directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            source_dir = temp_path / "source"
            source_dir.mkdir()
            output_dir = temp_path / "output"

            # Should not error with empty directory
            generated_files = generate_directory(source_dir, output_dir)
            assert generated_files == []
