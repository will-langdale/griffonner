"""Tests for module-based local plugin discovery."""

import sys
from unittest.mock import Mock

from griffonner.plugins.manager import PluginManager


class TestModuleBasedLocalPlugins:
    """Test module-based local plugin discovery."""

    def test_local_plugins_from_module_with_filters_and_processors(self, tmp_path):
        """Test loading both filters and processors from a local module."""
        # Create a temporary Python module
        module_dir = tmp_path / "test_module"
        module_dir.mkdir()

        # Create __init__.py to make it a package
        (module_dir / "__init__.py").write_text("")

        # Create a module with both filters and processors
        plugin_file = module_dir / "docs_plugins.py"
        plugin_file.write_text('''
"""Test module with both filters and processors."""
from typing import Any, Dict, Tuple, Union
from griffe import Alias, Object as GriffeObject
from griffonner.plugins.base import BaseProcessor

def uppercase_filter(value):
    """Convert value to uppercase."""
    return str(value).upper()

def format_signature(sig):
    """Format function signature nicely."""
    return sig.replace("(", "(\\n    ").replace(", ", ",\\n    ")

class MetadataProcessor(BaseProcessor):
    """Adds custom metadata to template context."""
    
    @property
    def name(self) -> str:
        return "metadata_processor"
    
    @property
    def priority(self) -> int:
        return 75
    
    def process(
        self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
    ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        context["custom_metadata"] = {
            "processed": True,
            "obj_name": getattr(griffe_obj, "name", "unknown")
        }
        return griffe_obj, context

class SimpleProcessor:
    """Simple processor without inheriting from BaseProcessor."""
    
    @property
    def name(self) -> str:
        return "simple_processor"
    
    def process(self, griffe_obj, context):
        context["simple_data"] = "processed by simple processor"
        return griffe_obj, context

def _private_function():
    """Private functions should not be loaded as filters."""
    return "private"

class _PrivateProcessor:
    """Private classes should not be loaded."""
    pass

class NotAProcessor:
    """Classes without process method should not be loaded."""
    pass
''')

        # Add the temporary directory to Python path
        sys.path.insert(0, str(tmp_path))

        try:
            # Create plugin manager with the test module
            plugin_manager = PluginManager(
                local_plugin_modules=["test_module.docs_plugins"]
            )

            # Get loaded plugins
            filters = plugin_manager.get_filters()
            processors = plugin_manager.get_processors()

            # Should load both filters
            assert "uppercase_filter" in filters
            assert "format_signature" in filters
            assert "test_module.docs_plugins.uppercase_filter" in filters
            assert "test_module.docs_plugins.format_signature" in filters

            # Should load both processors
            assert "metadata_processor" in processors
            assert "simple_processor" in processors
            assert "test_module.docs_plugins.metadata_processor" in processors
            assert "test_module.docs_plugins.simple_processor" in processors

            # Should not load private items or invalid processors
            assert "_private_function" not in filters
            assert "_PrivateProcessor" not in processors
            assert "NotAProcessor" not in processors

            # Test that filters work
            assert filters["uppercase_filter"]("hello") == "HELLO"
            assert "\n    " in filters["format_signature"]("func(a, b)")

            # Test that processors work
            mock_obj = Mock()
            mock_obj.name = "test_object"

            # Test metadata processor
            metadata_proc = processors["metadata_processor"]
            result_obj, result_context = metadata_proc.process(mock_obj, {})
            assert result_obj is mock_obj
            assert "custom_metadata" in result_context
            assert result_context["custom_metadata"]["processed"] is True
            assert result_context["custom_metadata"]["obj_name"] == "test_object"

            # Test simple processor
            simple_proc = processors["simple_processor"]
            result_obj, result_context = simple_proc.process(mock_obj, {})
            assert result_obj is mock_obj
            assert result_context["simple_data"] == "processed by simple processor"

        finally:
            # Clean up sys.path
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_multiple_local_plugin_modules(self, tmp_path):
        """Test loading plugins from multiple modules."""
        # Create two modules
        module1_dir = tmp_path / "module1"
        module1_dir.mkdir()
        (module1_dir / "__init__.py").write_text("")

        module2_dir = tmp_path / "module2"
        module2_dir.mkdir()
        (module2_dir / "__init__.py").write_text("")

        # Create plugins in first module
        (module1_dir / "plugins.py").write_text("""
def filter_one(value):
    return f"one: {value}"

class ProcessorOne:
    @property
    def name(self):
        return "processor_one"
    
    def process(self, obj, context):
        context["from_one"] = True
        return obj, context
""")

        # Create plugins in second module
        (module2_dir / "plugins.py").write_text("""
def filter_two(value):
    return f"two: {value}"

class ProcessorTwo:
    @property
    def name(self):
        return "processor_two"
    
    def process(self, obj, context):
        context["from_two"] = True
        return obj, context
""")

        sys.path.insert(0, str(tmp_path))

        try:
            plugin_manager = PluginManager(
                local_plugin_modules=["module1.plugins", "module2.plugins"]
            )

            filters = plugin_manager.get_filters()
            processors = plugin_manager.get_processors()

            # Should have filters from both modules
            assert "filter_one" in filters
            assert "filter_two" in filters
            assert "module1.plugins.filter_one" in filters
            assert "module2.plugins.filter_two" in filters

            # Should have processors from both modules
            assert "processor_one" in processors
            assert "processor_two" in processors
            assert "module1.plugins.processor_one" in processors
            assert "module2.plugins.processor_two" in processors

            # Test functionality
            assert filters["filter_one"]("test") == "one: test"
            assert filters["filter_two"]("test") == "two: test"

        finally:
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_import_error_handling(self):
        """Test graceful handling of import errors."""
        # Try to load a non-existent module
        plugin_manager = PluginManager(local_plugin_modules=["non.existent.module"])

        # Should not raise an exception, just log warnings
        filters = plugin_manager.get_filters()
        processors = plugin_manager.get_processors()

        # Should not have any local plugins from the failed import
        local_filters = [name for name in filters if "non.existent.module" in name]
        local_processors = [
            name for name in processors if "non.existent.module" in name
        ]

        assert len(local_filters) == 0
        assert len(local_processors) == 0

    def test_processor_without_name_property(self, tmp_path):
        """Test processor class without explicit name property."""
        module_dir = tmp_path / "test_unnamed"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")

        (module_dir / "plugins.py").write_text('''
class MyCustomProcessor:
    """A processor without explicit name property."""
    
    def process(self, obj, context):
        context["custom_processed"] = True
        return obj, context
''')

        sys.path.insert(0, str(tmp_path))

        try:
            plugin_manager = PluginManager(
                local_plugin_modules=["test_unnamed.plugins"]
            )
            processors = plugin_manager.get_processors()

            # Should use snake_case version of class name
            assert "my_custom_processor" in processors
            assert "test_unnamed.plugins.my_custom_processor" in processors

            # Test functionality
            processor = processors["my_custom_processor"]
            mock_obj = Mock()
            result_obj, result_context = processor.process(mock_obj, {})

            assert result_obj is mock_obj
            assert result_context["custom_processed"] is True

        finally:
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_name_conflicts_between_modules(self, tmp_path):
        """Test handling of name conflicts between modules."""
        # Create two modules with same function names
        module1_dir = tmp_path / "mod1"
        module1_dir.mkdir()
        (module1_dir / "__init__.py").write_text("")

        module2_dir = tmp_path / "mod2"
        module2_dir.mkdir()
        (module2_dir / "__init__.py").write_text("")

        (module1_dir / "plugins.py").write_text("""
def format_text(value):
    return f"mod1: {value}"

class TextProcessor:
    @property
    def name(self):
        return "text_processor"
    
    def process(self, obj, context):
        context["processed_by"] = "mod1"
        return obj, context
""")

        (module2_dir / "plugins.py").write_text("""
def format_text(value):
    return f"mod2: {value}"

class TextProcessor:
    @property
    def name(self):
        return "text_processor"
    
    def process(self, obj, context):
        context["processed_by"] = "mod2"
        return obj, context
""")

        sys.path.insert(0, str(tmp_path))

        try:
            # Load first module, then second
            plugin_manager = PluginManager(
                local_plugin_modules=["mod1.plugins", "mod2.plugins"]
            )

            filters = plugin_manager.get_filters()
            processors = plugin_manager.get_processors()

            # Should have qualified names for both
            assert "mod1.plugins.format_text" in filters
            assert "mod2.plugins.format_text" in filters
            assert "mod1.plugins.text_processor" in processors
            assert "mod2.plugins.text_processor" in processors

            # Simple names should belong to first loaded (mod1)
            assert "format_text" in filters
            assert "text_processor" in processors
            assert filters["format_text"]("test") == "mod1: test"

            mock_obj = Mock()
            result_obj, result_context = processors["text_processor"].process(
                mock_obj, {}
            )
            assert result_context["processed_by"] == "mod1"

        finally:
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_empty_module_list(self):
        """Test plugin manager with empty module list."""
        plugin_manager = PluginManager(local_plugin_modules=[])

        # Should work normally, just no local plugins
        filters = plugin_manager.get_filters()

        # May have entry point plugins, but no local ones
        local_filters = [
            name for name in filters if "." in name and not name.startswith("bundle.")
        ]

        # With empty list, should not have any local plugins
        # (assuming no modules with dots in their simple names)
        assert len([f for f in local_filters if not f.count(".") > 1]) == 0

    def test_processor_instantiation_failure(self, tmp_path):
        """Test handling of processor classes that fail to instantiate."""
        module_dir = tmp_path / "test_failing"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")

        (module_dir / "plugins.py").write_text('''
class FailingProcessor:
    """A processor that fails to instantiate."""
    
    def __init__(self):
        raise RuntimeError("Cannot instantiate this processor")
    
    @property
    def name(self):
        return "failing_processor"
    
    def process(self, obj, context):
        return obj, context

class WorkingProcessor:
    """A processor that works fine."""
    
    @property
    def name(self):
        return "working_processor"
    
    def process(self, obj, context):
        context["working"] = True
        return obj, context
''')

        sys.path.insert(0, str(tmp_path))

        try:
            plugin_manager = PluginManager(
                local_plugin_modules=["test_failing.plugins"]
            )
            processors = plugin_manager.get_processors()

            # Should not have the failing processor
            assert "failing_processor" not in processors
            assert "test_failing.plugins.failing_processor" not in processors

            # Should have the working processor
            assert "working_processor" in processors
            assert "test_failing.plugins.working_processor" in processors

        finally:
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))

    def test_integration_with_entry_point_plugins(self, tmp_path):
        """Test that local plugins work alongside entry point plugins."""
        module_dir = tmp_path / "integration_test"
        module_dir.mkdir()
        (module_dir / "__init__.py").write_text("")

        (module_dir / "plugins.py").write_text("""
def local_filter(value):
    return f"local: {value}"

class LocalProcessor:
    @property
    def name(self):
        return "local_processor"
    
    def process(self, obj, context):
        context["local"] = True
        return obj, context
""")

        sys.path.insert(0, str(tmp_path))

        try:
            plugin_manager = PluginManager(
                local_plugin_modules=["integration_test.plugins"]
            )

            filters = plugin_manager.get_filters()
            processors = plugin_manager.get_processors()

            # Should have local plugins
            assert "local_filter" in filters
            assert "local_processor" in processors

            # May also have entry point plugins (but we can't guarantee any specific)
            # The important thing is that loading doesn't fail
            plugin_list = plugin_manager.list_plugins()
            assert isinstance(plugin_list, dict)
            assert "processors" in plugin_list
            assert "filters" in plugin_list
            assert "bundles" in plugin_list

        finally:
            if str(tmp_path) in sys.path:
                sys.path.remove(str(tmp_path))
