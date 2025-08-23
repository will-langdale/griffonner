"""Tests for plugin manager."""

from unittest.mock import Mock, patch

import pytest

from griffonner.plugins.base import BaseBundle, BaseProcessor
from griffonner.plugins.manager import PluginError, PluginLoadError, PluginManager


class MockProcessor(BaseProcessor):
    """Mock processor for testing."""

    def __init__(self, name: str, priority: int = 100):
        self._name = name
        self._priority = priority

    @property
    def name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    def process(self, griffe_obj, context):
        context[f"processed_by_{self.name}"] = True
        return griffe_obj, context


class MockBundle(BaseBundle):
    """Mock bundle for testing."""

    def __init__(self, name: str, version: str = "1.0.0"):
        self._name = name
        self._version = version

    @property
    def name(self) -> str:
        return self._name

    @property
    def version(self) -> str:
        return self._version

    @property
    def description(self) -> str:
        return f"Mock bundle {self._name}"

    def get_processors(self):
        return {"bundle_proc": MockProcessor(f"{self._name}_proc")}

    def get_filters(self):
        return {"bundle_filter": lambda x: f"filtered_{x}"}

    def get_template_paths(self):
        return [f"templates/{self._name}/"]


def mock_filter_func(value):
    """Mock filter function."""
    return str(value).upper()


class TestPluginManager:
    """Tests for PluginManager class."""

    def test_init(self):
        """Test plugin manager initialisation."""
        manager = PluginManager()

        assert manager._processors == {}
        assert manager._filters == {}
        assert manager._bundles == {}
        assert manager._loaded is False

    @patch("importlib.metadata.entry_points")
    def test_load_plugins_empty(self, mock_entry_points):
        """Test loading plugins when no entry points exist."""
        # Mock empty entry points dictionary
        mock_entry_points.return_value = {}

        manager = PluginManager()
        manager.load_plugins()

        assert manager._loaded is True
        assert manager._processors == {}
        assert manager._filters == {}
        assert manager._bundles == {}

    @patch("importlib.metadata.entry_points")
    def test_load_processors(self, mock_entry_points):
        """Test loading processor plugins."""
        # Mock entry point
        mock_entry_point = Mock()
        mock_entry_point.name = "test_processor"
        mock_entry_point.load.return_value = MockProcessor("test_processor")

        # Mock entry points as a dict (Python 3.9 style)
        mock_entry_points.return_value = {
            "griffonner.processors": [mock_entry_point],
            "griffonner.filters": [],
            "griffonner.bundles": [],
        }

        manager = PluginManager()
        manager.load_plugins()

        assert "test_processor" in manager._processors
        assert isinstance(manager._processors["test_processor"], MockProcessor)
        assert manager._loaded is True

    @patch("importlib.metadata.entry_points")
    def test_load_filters(self, mock_entry_points):
        """Test loading filter plugins."""
        # Mock entry point
        mock_entry_point = Mock()
        mock_entry_point.name = "test_filter"
        mock_entry_point.load.return_value = mock_filter_func

        # Mock entry points as a dict (Python 3.9 style)
        mock_entry_points.return_value = {
            "griffonner.processors": [],
            "griffonner.filters": [mock_entry_point],
            "griffonner.bundles": [],
        }

        manager = PluginManager()
        manager.load_plugins()

        assert "test_filter" in manager._filters
        assert manager._filters["test_filter"] is mock_filter_func
        assert manager._loaded is True

    @patch("importlib.metadata.entry_points")
    def test_load_bundles(self, mock_entry_points):
        """Test loading bundle plugins."""
        # Mock entry point
        mock_entry_point = Mock()
        mock_entry_point.name = "test_bundle"
        mock_entry_point.load.return_value = MockBundle("test_bundle")

        # Mock entry points as a dict (Python 3.9 style)
        mock_entry_points.return_value = {
            "griffonner.processors": [],
            "griffonner.filters": [],
            "griffonner.bundles": [mock_entry_point],
        }

        manager = PluginManager()
        manager.load_plugins()

        assert "test_bundle" in manager._bundles
        assert isinstance(manager._bundles["test_bundle"], MockBundle)

        # Check that bundle components were loaded
        assert "test_bundle.bundle_proc" in manager._processors
        assert "test_bundle.bundle_filter" in manager._filters

        assert manager._loaded is True

    @patch("importlib.metadata.entry_points")
    def test_load_plugin_error(self, mock_entry_points):
        """Test handling of plugin loading errors."""
        # Mock entry point that raises an error
        mock_entry_point = Mock()
        mock_entry_point.name = "broken_processor"
        mock_entry_point.load.side_effect = ImportError("Module not found")

        # Mock entry points as a dict (Python 3.9 style)
        mock_entry_points.return_value = {
            "griffonner.processors": [mock_entry_point],
            "griffonner.filters": [],
            "griffonner.bundles": [],
        }

        manager = PluginManager()

        with pytest.raises(
            PluginLoadError, match="Failed to load plugin 'broken_processor'"
        ):
            manager.load_plugins()

    def test_get_processors(self):
        """Test getting processors with lazy loading."""
        manager = PluginManager()

        # Manually add a processor to test
        test_processor = MockProcessor("manual")
        manager._processors = {"manual": test_processor}
        manager._loaded = True

        processors = manager.get_processors()

        assert "manual" in processors
        assert processors["manual"] is test_processor
        assert processors is not manager._processors  # Should be a copy

    def test_get_filters(self):
        """Test getting filters with lazy loading."""
        manager = PluginManager()

        # Manually add a filter to test
        manager._filters = {"test": mock_filter_func}
        manager._loaded = True

        filters = manager.get_filters()

        assert "test" in filters
        assert filters["test"] is mock_filter_func
        assert filters is not manager._filters  # Should be a copy

    def test_get_bundles(self):
        """Test getting bundles with lazy loading."""
        manager = PluginManager()

        # Manually add a bundle to test
        test_bundle = MockBundle("test")
        manager._bundles = {"test": test_bundle}
        manager._loaded = True

        bundles = manager.get_bundles()

        assert "test" in bundles
        assert bundles["test"] is test_bundle
        assert bundles is not manager._bundles  # Should be a copy

    def test_process_griffe_object_no_processors(self):
        """Test processing with no processors available."""
        manager = PluginManager()
        manager._loaded = True

        obj = object()
        context = {"test": "value"}

        result_obj, result_context = manager.process_griffe_object(obj, context)

        assert result_obj is obj
        assert result_context == {"test": "value"}

    def test_process_griffe_object_with_processors(self):
        """Test processing with multiple processors."""
        manager = PluginManager()

        # Add processors with different priorities
        proc1 = MockProcessor("first", priority=50)  # Higher priority (runs first)
        proc2 = MockProcessor("second", priority=150)  # Lower priority (runs second)

        manager._processors = {"first": proc1, "second": proc2}
        manager._loaded = True

        obj = object()
        context = {"test": "value"}

        result_obj, result_context = manager.process_griffe_object(obj, context)

        assert result_obj is obj
        assert result_context["test"] == "value"
        assert result_context["processed_by_first"] is True
        assert result_context["processed_by_second"] is True

    def test_process_griffe_object_specific_processors(self):
        """Test processing with specific processor names."""
        manager = PluginManager()

        proc1 = MockProcessor("first")
        proc2 = MockProcessor("second")

        manager._processors = {"first": proc1, "second": proc2}
        manager._loaded = True

        obj = object()
        context = {"test": "value"}

        # Only use the second processor
        result_obj, result_context = manager.process_griffe_object(
            obj, context, processor_names=["second"]
        )

        assert result_obj is obj
        assert result_context["test"] == "value"
        assert "processed_by_first" not in result_context
        assert result_context["processed_by_second"] is True

    def test_process_griffe_object_unknown_processor(self):
        """Test processing with unknown processor name."""
        manager = PluginManager()
        manager._loaded = True

        obj = object()
        context = {"test": "value"}

        with pytest.raises(PluginError, match="Processor 'unknown' not found"):
            manager.process_griffe_object(obj, context, processor_names=["unknown"])

    def test_list_plugins(self):
        """Test listing all plugins."""
        manager = PluginManager()

        # Manually add some plugins
        manager._processors = {"proc1": MockProcessor("proc1")}
        manager._filters = {"filter1": mock_filter_func}
        manager._bundles = {"bundle1": MockBundle("bundle1")}
        manager._loaded = True

        plugins = manager.list_plugins()

        expected = {
            "processors": ["proc1"],
            "filters": ["filter1"],
            "bundles": ["bundle1"],
        }

        assert plugins == expected

    def test_get_bundle_info_existing(self):
        """Test getting info for an existing bundle."""
        manager = PluginManager()

        bundle = MockBundle("test_bundle", "2.0.0")
        manager._bundles = {"test_bundle": bundle}
        manager._loaded = True

        info = manager.get_bundle_info("test_bundle")

        assert info is not None
        assert info["name"] == "test_bundle"
        assert info["version"] == "2.0.0"
        assert info["description"] == "Mock bundle test_bundle"
        assert info["processors"] == ["bundle_proc"]
        assert info["filters"] == ["bundle_filter"]
        assert info["template_paths"] == ["templates/test_bundle/"]

    def test_get_bundle_info_nonexistent(self):
        """Test getting info for a non-existent bundle."""
        manager = PluginManager()
        manager._loaded = True

        info = manager.get_bundle_info("nonexistent")

        assert info is None
