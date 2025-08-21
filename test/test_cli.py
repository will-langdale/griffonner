"""Tests for cli module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from typer.testing import CliRunner

from griffonner.cli import app


runner = CliRunner()


class TestGenerateCommand:
    """Tests for generate command."""
    
    def test_generate_file_success(self):
        """Tests successful file generation via CLI."""
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
            
            result = runner.invoke(app, [
                "generate",
                str(source_file),
                "--output", str(output_dir),
                "--template-dir", str(template_dir)
            ])
            
            assert result.exit_code == 0
            assert "✅ Generated 1 files:" in result.stdout
            assert "test.md" in result.stdout
            
            # Verify file was actually created
            # Core logic creates subdirectory based on source file's parent
            expected_subdir = source_file.parent.name
            output_file = output_dir / expected_subdir / "test.md"
            assert output_file.exists()
    
    def test_generate_directory_success(self):
        """Tests successful directory generation via CLI."""
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
            
            result = runner.invoke(app, [
                "generate",
                str(pages_dir),
                "--output", str(output_dir),
                "--template-dir", str(template_dir)
            ])
            
            assert result.exit_code == 0
            assert "✅ Generated 1 files:" in result.stdout
    
    def test_generate_nonexistent_source(self):
        """Tests error when source doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            nonexistent = temp_path / "nonexistent.md"
            output_dir = temp_path / "output"
            
            result = runner.invoke(app, [
                "generate", 
                str(nonexistent),
                "--output", str(output_dir)
            ])
            
            assert result.exit_code == 1
            assert "❌ Generation failed:" in result.output
    
    def test_generate_with_default_output_dir(self):
        """Tests generate command with default output directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template in default location
            template_dir = temp_path / "docs" / "templates"
            template_dir.mkdir(parents=True)
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
            
            # Change to temp directory so default paths work
            import os
            old_cwd = os.getcwd()
            try:
                os.chdir(temp_path)
                
                result = runner.invoke(app, [
                    "generate",
                    str(source_file.name)  # Use relative path
                ])
                
                # Should succeed even though we didn't specify output dir
                assert result.exit_code == 0
                
            finally:
                os.chdir(old_cwd)


class TestTemplatesCommand:
    """Tests for templates command."""
    
    def test_templates_list_success(self):
        """Tests successful template listing."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template directory with templates
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            (template_dir / "simple.md.jinja2").write_text("Simple")
            (template_dir / "complex.html.jinja2").write_text("Complex")
            
            # Create subdirectory
            subdir = template_dir / "python"
            subdir.mkdir()
            (subdir / "module.md.jinja2").write_text("Module")
            
            result = runner.invoke(app, [
                "templates",
                "--template-dir", str(template_dir)
            ])
            
            assert result.exit_code == 0
            assert "📋 Found 3 templates:" in result.stdout
            assert "simple.md.jinja2" in result.stdout
            assert "complex.html.jinja2" in result.stdout
            assert "python/module.md.jinja2" in result.stdout
    
    def test_templates_list_with_pattern(self):
        """Tests template listing with custom pattern."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            (template_dir / "test.md.jinja2").write_text("MD template")
            (template_dir / "test.html.jinja2").write_text("HTML template")
            (template_dir / "test.j2").write_text("J2 template")
            
            result = runner.invoke(app, [
                "templates",
                "--template-dir", str(template_dir),
                "--pattern", "**/*.j2"
            ])
            
            assert result.exit_code == 0
            assert "📋 Found 1 templates:" in result.stdout
            assert "test.j2" in result.stdout
            assert "test.md.jinja2" not in result.stdout
    
    def test_templates_list_no_templates_found(self):
        """Tests template listing when no templates exist."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create empty template directory
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            result = runner.invoke(app, [
                "templates",
                "--template-dir", str(template_dir)
            ])
            
            assert result.exit_code == 0
            assert "No templates found" in result.stdout
    
    def test_templates_list_error(self):
        """Tests error handling in templates command."""
        # Test with nonexistent directory - should still work since TemplateLoader
        # handles nonexistent directories gracefully
        result = runner.invoke(app, [
            "templates",
            "--template-dir", "/definitely/nonexistent/directory"
        ])
        
        assert result.exit_code == 0
        assert "No templates found" in result.stdout


class TestWatchCommand:
    """Tests for watch command (Phase 2 - not implemented)."""
    
    def test_watch_not_implemented(self):
        """Tests that watch command returns not implemented error."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            pages_dir = temp_path / "pages"
            pages_dir.mkdir()
            output_dir = temp_path / "output"
            
            result = runner.invoke(app, [
                "watch",
                str(pages_dir),
                "--output", str(output_dir)
            ])
            
            assert result.exit_code == 1
            assert "❌ Watch mode not yet implemented" in result.output


class TestCLIIntegration:
    """Integration tests for CLI."""
    
    def test_help_message(self):
        """Tests that help message is displayed."""
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "Template-first Python documentation generator" in result.stdout
        assert "generate" in result.stdout
        assert "templates" in result.stdout
        assert "watch" in result.stdout
    
    def test_command_help_messages(self):
        """Tests help messages for individual commands."""
        # Test generate help
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate documentation from source files" in result.stdout
        
        # Test templates help
        result = runner.invoke(app, ["templates", "--help"])
        assert result.exit_code == 0
        assert "List available templates" in result.stdout
        
        # Test watch help
        result = runner.invoke(app, ["watch", "--help"])
        assert result.exit_code == 0
        assert "Watch source directory for changes" in result.stdout