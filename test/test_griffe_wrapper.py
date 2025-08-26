"""Tests for griffe_wrapper module."""

import textwrap
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

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
            module_content = textwrap.dedent('''\
                """Test module."""

                def hello_world():
                    """Say hello to the world."""
                    return "Hello, World!"

                class TestClass:
                    """A test class."""
                    
                    def test_method(self):
                        """A test method."""
                        return "test"

                CONSTANT = 42
                ''')

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
            init_file.write_text(
                '"""Test package."""\n\nfrom .module import test_function\n'
            )

            # Create module.py
            module_file = package_dir / "module.py"
            module_file.write_text(
                textwrap.dedent('''\
                """Test module in package."""

                def test_function():
                    """A test function."""
                    return "test"
                ''')
            )

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
            module_file.write_text(
                textwrap.dedent('''\
                """Custom module."""

                def custom_function():
                    """A custom function."""
                    return "custom"
                ''')
            )

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

    def test_griffe_config_structure(self):
        """Tests the griffe config structure with method calls."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a simple module
            module_content = textwrap.dedent('''\
                """Test module."""

                def hello():
                    """Say hello."""
                    pass
                ''')

            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)

            # Use new config structure with loader options and method calls
            griffe_config = {
                "loader": {
                    "allow_inspection": True,
                    "store_source": False,
                    "load": {"submodules": True},
                    "resolve_aliases": {"external": False},
                }
            }

            griffe_obj = load_griffe_object(
                "test_module",
                search_paths=[temp_path],
                griffe_config=griffe_config,
            )

            assert griffe_obj is not None
            assert griffe_obj.name == "test_module"
            assert griffe_obj.kind.value == "module"
            assert "hello" in griffe_obj.members

    def test_contextlib_import_without_resolve_aliases(self):
        """Tests the contextlib issue - no alias resolution means no errors."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Reproduce the exact example from the GitHub issue
            module_content = textwrap.dedent('''\
                import contextlib

                def hello():
                    """Say hello."""
                    pass
                ''')

            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)

            # Use new structure without resolve_aliases method call
            griffe_config = {
                "loader": {
                    "allow_inspection": True,
                    "load": {"submodules": False},
                    # Note: no resolve_aliases call = no alias resolution errors
                }
            }

            griffe_obj = load_griffe_object(
                "test_module",
                search_paths=[temp_path],
                griffe_config=griffe_config,
            )

            assert griffe_obj is not None
            assert griffe_obj.name == "test_module"
            assert griffe_obj.kind.value == "module"

            # The module should have both hello function and contextlib import
            assert "hello" in griffe_obj.members
            assert "contextlib" in griffe_obj.members

            # The contextlib member should be an alias (not resolved)
            contextlib_member = griffe_obj.members["contextlib"]
            from griffe import Alias

            assert isinstance(contextlib_member, Alias)

    def test_empty_config_works(self):
        """Tests that empty/default config works."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a simple module
            module_content = textwrap.dedent('''\
                """Simple test module."""

                def simple_function():
                    """A simple function."""
                    pass
                ''')

            module_file = temp_path / "simple_module.py"
            module_file.write_text(module_content)

            # Empty config should work
            griffe_obj = load_griffe_object(
                "simple_module", search_paths=[temp_path], griffe_config={}
            )

            assert griffe_obj is not None
            assert griffe_obj.name == "simple_module"
            assert "simple_function" in griffe_obj.members

    def test_invalid_loader_options(self):
        """Tests that invalid loader options raise appropriate errors."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            module_content = textwrap.dedent('''\
                """Test module."""

                def hello():
                    """Say hello."""
                    pass
                ''')

            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)

            # Invalid loader option should raise ModuleLoadError
            griffe_config = {"loader": {"invalid_option": "invalid_value"}}

            with pytest.raises(ModuleLoadError, match="Invalid Griffe loader options"):
                load_griffe_object(
                    "test_module",
                    search_paths=[temp_path],
                    griffe_config=griffe_config,
                )

    def test_invalid_load_options(self):
        """Tests that invalid load options raise appropriate errors."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            module_content = textwrap.dedent('''\
                """Test module."""

                def hello():
                    """Say hello."""
                    pass
                ''')

            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)

            # Invalid load option should raise ModuleLoadError
            griffe_config = {
                "loader": {"load": {"invalid_load_option": "invalid_value"}}
            }

            with pytest.raises(ModuleLoadError, match="Invalid load options"):
                load_griffe_object(
                    "test_module",
                    search_paths=[temp_path],
                    griffe_config=griffe_config,
                )

    def test_method_call_failure(self):
        """Tests that method call failures are handled properly."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            module_content = textwrap.dedent('''\
                """Test module."""

                def hello():
                    """Say hello."""
                    pass
                ''')

            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)

            # Invalid method args should cause method failure
            griffe_config = {
                "loader": {"resolve_aliases": {"invalid_arg": "invalid_value"}}
            }

            with pytest.raises(
                ModuleLoadError, match="Griffe method 'resolve_aliases' failed"
            ):
                load_griffe_object(
                    "test_module",
                    search_paths=[temp_path],
                    griffe_config=griffe_config,
                )

    def test_nonexistent_method_warning(self):
        """Tests that nonexistent methods are skipped with warning."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            module_content = textwrap.dedent('''\
                """Test module."""

                def hello():
                    """Say hello."""
                    pass
                ''')

            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)

            # Nonexistent method should be skipped (not error)
            griffe_config = {
                "loader": {"nonexistent_method": {"some_arg": "some_value"}}
            }

            # Should complete without error, just log warning
            griffe_obj = load_griffe_object(
                "test_module",
                search_paths=[temp_path],
                griffe_config=griffe_config,
            )

            assert griffe_obj is not None
            assert griffe_obj.name == "test_module"
            assert "hello" in griffe_obj.members

    def test_various_loader_options(self):
        """Tests various valid loader initialization options."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            module_content = textwrap.dedent('''\
                """Test module with docstring."""

                def hello():
                    """Say hello."""
                    pass
                ''')

            module_file = temp_path / "test_module.py"
            module_file.write_text(module_content)

            # Test various loader options
            griffe_config = {
                "loader": {
                    "allow_inspection": False,
                    "store_source": True,
                    "load": {"submodules": False},
                }
            }

            griffe_obj = load_griffe_object(
                "test_module",
                search_paths=[temp_path],
                griffe_config=griffe_config,
            )

            assert griffe_obj is not None
            assert griffe_obj.name == "test_module"
            assert "hello" in griffe_obj.members
