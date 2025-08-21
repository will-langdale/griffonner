"""Tests for griffe_wrapper module."""

import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from griffonner.griffe_wrapper import (
    GriffeError,
    ModuleLoadError,
    load_griffe_object,
)


class TestGriffeError:
    """Tests for GriffeError exception."""
    
    def test_griffe_error_inheritance(self):
        """Tests that GriffeError inherits from Exception."""
        assert issubclass(GriffeError, Exception)
    
    def test_module_load_error_inheritance(self):
        """Tests that ModuleLoadError inherits from GriffeError."""
        assert issubclass(ModuleLoadError, GriffeError)


class TestLoadGriffeObject:
    """Tests for load_griffe_object function."""
    
    def test_load_builtin_module(self):
        """Tests loading a built-in Python module."""
        # Load the os module which should always be available
        griffe_obj = load_griffe_object("os")
        
        assert griffe_obj is not None
        assert griffe_obj.name == "os"
        assert griffe_obj.kind.value == "module"
    
    def test_load_standard_library_module(self):
        """Tests loading a standard library module."""
        # Load pathlib which should always be available
        griffe_obj = load_griffe_object("pathlib")
        
        assert griffe_obj is not None
        assert griffe_obj.name == "pathlib"
        assert griffe_obj.kind.value == "module"
        # Should have some members
        assert hasattr(griffe_obj, "members")
    
    def test_load_nonexistent_module(self):
        """Tests error when loading non-existent module."""
        with pytest.raises(ModuleLoadError):
            load_griffe_object("definitely_nonexistent_module_12345")
    
    def test_load_local_module_by_name(self):
        """Tests loading a local module by name with search paths."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a simple Python module
            module_content = '''"""Test module."""

def hello_world():
    """Say hello to the world."""
    return "Hello, World!"

class TestClass:
    """A test class."""
    
    def test_method(self):
        """A test method."""
        return "test"

CONSTANT = 42
'''
            
            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)
            
            # Load the module by name with search path
            griffe_obj = load_griffe_object("test_module", search_paths=[temp_path])
            
            assert griffe_obj is not None
            assert griffe_obj.name == "test_module"
            assert griffe_obj.kind.value == "module"
            
            # Check that members were parsed
            assert hasattr(griffe_obj, "members")
            member_names = list(griffe_obj.members.keys())
            assert "hello_world" in member_names
            assert "TestClass" in member_names
            assert "CONSTANT" in member_names
            
            # Check function details
            hello_func = griffe_obj.members["hello_world"]
            assert hello_func.kind.value == "function"
            assert hello_func.docstring is not None
            
            # Check class details
            test_class = griffe_obj.members["TestClass"]
            assert test_class.kind.value == "class"
            assert "test_method" in test_class.members
    
    def test_load_package_by_name(self):
        """Tests loading a package by name."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create package structure
            package_dir = temp_path / "test_package"
            package_dir.mkdir()
            
            # Create __init__.py
            init_file = package_dir / "__init__.py"
            init_file.write_text('"""Test package."""\n\nfrom .module import test_function\n')
            
            # Create module.py
            module_file = package_dir / "module.py"
            module_file.write_text('''"""Test module in package."""

def test_function():
    """A test function."""
    return "test"
''')
            
            # Load the package by name with search path
            griffe_obj = load_griffe_object("test_package", search_paths=[temp_path])
            
            assert griffe_obj is not None
            assert griffe_obj.name == "test_package"
            assert griffe_obj.kind.value == "module"  # Packages are modules in Griffe
    
    def test_custom_search_paths(self):
        """Tests that custom search paths are used."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a module in a subdirectory
            subdir = temp_path / "custom_dir"
            subdir.mkdir()
            
            module_file = subdir / "custom_module.py"
            module_file.write_text('''"""Custom module."""

def custom_function():
    """A custom function."""
    return "custom"
''')
            
            # Load with custom search path
            griffe_obj = load_griffe_object("custom_module", search_paths=[subdir])
            
            assert griffe_obj is not None
            assert griffe_obj.name == "custom_module"
            assert "custom_function" in griffe_obj.members
    
    def test_load_with_module_name_only(self):
        """Tests loading with just module name (no search paths)."""
        # This should work for standard library modules
        griffe_obj = load_griffe_object("json")
        
        assert griffe_obj is not None
        assert griffe_obj.name == "json"
        assert griffe_obj.kind.value == "module"
    
    def test_error_chaining(self):
        """Tests that exceptions are properly chained."""
        try:
            load_griffe_object("nonexistent_module_xyz_123")
        except ModuleLoadError as e:
            # Should have original exception in chain
            assert e.__cause__ is not None
        else:
            pytest.fail("Expected ModuleLoadError to be raised")