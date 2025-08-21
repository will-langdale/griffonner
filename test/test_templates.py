"""Tests for templates module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from griffonner.templates import (
    TemplateError,
    TemplateLoader,
    TemplateNotFoundError,
    TemplateValidationError,
)


class TestTemplateError:
    """Tests for template exceptions."""
    
    def test_template_error_inheritance(self):
        """Tests that TemplateError inherits from Exception."""
        assert issubclass(TemplateError, Exception)
    
    def test_template_not_found_error_inheritance(self):
        """Tests that TemplateNotFoundError inherits from TemplateError."""
        assert issubclass(TemplateNotFoundError, TemplateError)


class TestTemplateLoader:
    """Tests for TemplateLoader class."""
    
    def test_default_template_dirs(self):
        """Tests that default template directories are set."""
        loader = TemplateLoader()
        
        expected_dirs = [
            Path.cwd() / "docs" / "templates",
            Path.cwd() / "templates",
        ]
        
        # Should include default dirs (may include more from custom dirs)
        for expected_dir in expected_dirs:
            assert expected_dir in loader.template_dirs
    
    def test_custom_template_dirs(self):
        """Tests that custom template directories are added."""
        custom_dir = Path("/custom/template/dir")
        loader = TemplateLoader(template_dirs=[custom_dir])
        
        assert custom_dir in loader.template_dirs
    
    def test_load_template_success(self):
        """Tests successful template loading."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template file
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            template_content = """# {{ title }}

{{ description }}

## Functions

{% for func in functions %}
- {{ func.name }}: {{ func.docstring.summary }}
{% endfor %}
"""
            
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text(template_content)
            
            # Load template
            loader = TemplateLoader(template_dirs=[template_dir])
            template = loader.load_template("test.md.jinja2")
            
            assert template is not None
            assert template.name == "test.md.jinja2"
    
    def test_load_template_not_found(self):
        """Tests error when template is not found."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            loader = TemplateLoader(template_dirs=[template_dir])
            
            with pytest.raises(TemplateNotFoundError, match="Template not found"):
                loader.load_template("nonexistent.jinja2")
    
    def test_render_template_success(self):
        """Tests successful template rendering."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template file
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            template_content = """# {{ title }}

Description: {{ description }}

{% if functions %}
Functions:
{% for func in functions %}
- {{ func }}
{% endfor %}
{% endif %}
"""
            
            template_file = template_dir / "test.md.jinja2"
            template_file.write_text(template_content)
            
            # Render template
            loader = TemplateLoader(template_dirs=[template_dir])
            
            context = {
                "title": "Test Module",
                "description": "A test module for testing",
                "functions": ["func1", "func2", "func3"]
            }
            
            result = loader.render_template("test.md.jinja2", context)
            
            assert "# Test Module" in result
            assert "Description: A test module for testing" in result
            assert "- func1" in result
            assert "- func2" in result
            assert "- func3" in result
    
    def test_render_template_not_found(self):
        """Tests error when rendering non-existent template."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            loader = TemplateLoader(template_dirs=[template_dir])
            
            with pytest.raises(TemplateNotFoundError):
                loader.render_template("missing.jinja2", {})
    
    def test_render_template_error(self):
        """Tests error when template rendering fails."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template with runtime error
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            template_content = """# {{ title }}

{{ missing_variable.nonexistent_attribute }}
"""
            
            template_file = template_dir / "error.md.jinja2"
            template_file.write_text(template_content)
            
            loader = TemplateLoader(template_dirs=[template_dir])
            
            with pytest.raises(TemplateError, match="Template rendering failed"):
                loader.render_template("error.md.jinja2", {"title": "Test"})
    
    def test_find_templates(self):
        """Tests finding templates in directories."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create template structure
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            # Create various template files
            (template_dir / "simple.md.jinja2").write_text("Simple template")
            (template_dir / "complex.html.jinja2").write_text("HTML template")
            (template_dir / "not_template.txt").write_text("Not a template")
            
            # Create subdirectory with templates
            subdir = template_dir / "python" / "default"
            subdir.mkdir(parents=True)
            (subdir / "module.md.jinja2").write_text("Module template")
            (subdir / "class.j2").write_text("Class template")
            
            loader = TemplateLoader(template_dirs=[template_dir])
            templates = loader.find_templates()
            
            # Convert to set of string paths for easier comparison
            template_paths = {str(t) for t in templates}
            
            assert "simple.md.jinja2" in template_paths
            assert "complex.html.jinja2" in template_paths
            assert "python/default/module.md.jinja2" in template_paths
            assert "not_template.txt" not in template_paths  # Should exclude non-templates
    
    def test_find_templates_custom_pattern(self):
        """Tests finding templates with custom pattern."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            # Create files with different extensions
            (template_dir / "test1.md.jinja2").write_text("Template 1")
            (template_dir / "test2.html.jinja2").write_text("Template 2")
            (template_dir / "test3.j2").write_text("Template 3")
            
            loader = TemplateLoader(template_dirs=[template_dir])
            
            # Find only .j2 files
            j2_templates = loader.find_templates("**/*.j2")
            template_paths = {str(t) for t in j2_templates}
            
            assert "test3.j2" in template_paths
            assert "test1.md.jinja2" not in template_paths
            assert "test2.html.jinja2" not in template_paths
    
    def test_find_templates_no_duplicates(self):
        """Tests that duplicate templates are removed."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create two template directories with same file
            dir1 = temp_path / "templates1"
            dir2 = temp_path / "templates2"
            dir1.mkdir()
            dir2.mkdir()
            
            template_content = "Same template content"
            (dir1 / "same.md.jinja2").write_text(template_content)
            (dir2 / "same.md.jinja2").write_text(template_content)
            
            loader = TemplateLoader(template_dirs=[dir1, dir2])
            templates = loader.find_templates()
            
            # Should only find one instance despite being in both directories
            same_templates = [t for t in templates if t.name == "same.md.jinja2"]
            assert len(same_templates) == 1
    
    def test_jinja2_environment_settings(self):
        """Tests that Jinja2 environment is configured correctly."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            
            # Test autoescape is disabled (since we're generating docs, not HTML)
            template_content = """{{ html_content }}"""
            
            template_file = template_dir / "autoescape_test.jinja2"
            template_file.write_text(template_content)
            
            loader = TemplateLoader(template_dirs=[template_dir])
            result = loader.render_template("autoescape_test.jinja2", {"html_content": "<b>test</b>"})
            
            # Should not be escaped since autoescape=False
            assert result == "<b>test</b>"


class TestTemplateDiscovery:
    """Tests for enhanced template discovery (Phase 2)."""

    def test_find_default_template(self):
        """Test finding default templates by object kind."""
        loader = TemplateLoader()
        
        # Should find built-in templates
        module_template = loader.find_default_template("module")
        assert module_template == "python/default/module.md.jinja2"
        
        class_template = loader.find_default_template("class")
        assert class_template == "python/default/class.md.jinja2"
        
        function_template = loader.find_default_template("function")
        assert function_template == "python/default/function.md.jinja2"

    def test_find_default_template_nonexistent(self):
        """Test finding nonexistent default template."""
        loader = TemplateLoader()
        
        result = loader.find_default_template("nonexistent")
        assert result is None

    def test_get_available_template_sets(self):
        """Test getting available template sets."""
        loader = TemplateLoader()
        
        template_sets = loader.get_available_template_sets()
        assert "python/default" in template_sets

    def test_suggest_template(self):
        """Test template suggestion functionality."""
        loader = TemplateLoader()
        
        # Should suggest similar templates
        suggestions = loader.suggest_template("python/default/missing.md.jinja2")
        assert len(suggestions) > 0
        
        # Should find templates with similar names
        suggestions = loader.suggest_template("module.md.jinja2")
        assert any("module.md.jinja2" in s for s in suggestions)


class TestTemplateValidation:
    """Tests for template validation (Phase 2)."""

    def test_validate_valid_template(self):
        """Test validating a valid template."""
        loader = TemplateLoader()
        
        # Should not raise for valid built-in template
        loader.validate_template("python/default/module.md.jinja2")

    def test_validate_invalid_template(self):
        """Test validating an invalid template."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create invalid template
            template_dir = temp_path / "templates"
            template_dir.mkdir()
            template_file = template_dir / "invalid.jinja2"
            template_file.write_text("{{ unclosed")
            
            loader = TemplateLoader([template_dir])
            
            with pytest.raises(TemplateValidationError):
                loader.validate_template("invalid.jinja2")

    def test_validate_nonexistent_template(self):
        """Test validating nonexistent template."""
        loader = TemplateLoader()
        
        with pytest.raises(TemplateNotFoundError):
            loader.validate_template("nonexistent.jinja2")


class TestEnhancedErrorHandling:
    """Tests for enhanced error messages (Phase 2)."""

    def test_template_not_found_with_suggestions(self):
        """Test that template not found errors include helpful suggestions."""
        loader = TemplateLoader()
        
        with pytest.raises(TemplateNotFoundError) as exc_info:
            loader.load_template("python/default/missing.md.jinja2")
        
        error_msg = str(exc_info.value)
        assert "Template not found" in error_msg
        assert "Did you mean one of these?" in error_msg
        assert "Available template sets:" in error_msg

    def test_template_not_found_shows_available_sets(self):
        """Test that error shows available template sets."""
        loader = TemplateLoader()
        
        with pytest.raises(TemplateNotFoundError) as exc_info:
            loader.load_template("nonexistent/template.jinja2")
        
        error_msg = str(exc_info.value)
        assert "python/default/" in error_msg


class TestBuiltInTemplates:
    """Tests for built-in templates (Phase 2)."""

    def test_built_in_templates_exist(self):
        """Test that built-in templates exist and can be loaded."""
        loader = TemplateLoader()
        
        # Test all built-in templates can be loaded
        templates = ["module.md.jinja2", "class.md.jinja2", "function.md.jinja2"]
        for template_name in templates:
            template_path = f"python/default/{template_name}"
            template = loader.load_template(template_path)
            assert template is not None

    def test_built_in_template_rendering(self):
        """Test that built-in templates can render basic context."""
        loader = TemplateLoader()
        
        # Create mock Griffe object
        class MockObj:
            def __init__(self):
                self.name = "TestModule"
                self.docstring = None
                self.functions = {}
                self.classes = {}
                self.attributes = {}
        
        context = {"obj": MockObj(), "custom_vars": {}}
        
        # Should render without errors
        result = loader.render_template("python/default/module.md.jinja2", context)
        assert "TestModule" in result
        assert isinstance(result, str)

    def test_template_discovery_includes_built_in(self):
        """Test that template discovery includes built-in templates."""
        loader = TemplateLoader()
        
        templates = loader.find_templates()
        
        # Should find built-in templates
        built_in_templates = [
            "python/default/module.md.jinja2",
            "python/default/class.md.jinja2", 
            "python/default/function.md.jinja2"
        ]
        
        for template_path in built_in_templates:
            found_templates = [str(t) for t in templates]
            assert template_path in found_templates

    def test_built_in_templates_directory_structure(self):
        """Test that built-in templates follow expected directory structure."""
        loader = TemplateLoader()
        
        # Check that built-in template directory exists
        package_templates = Path(__file__).parent.parent / "templates"
        assert package_templates in loader.template_dirs
        
        # Template sets should include python/default
        template_sets = loader.get_available_template_sets()
        assert "python/default" in template_sets