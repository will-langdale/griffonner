"""Plugin manager for discovering and loading Griffonner plugins."""

import importlib.metadata
from typing import Any, Dict, List, Optional, Union

from griffe import Alias
from griffe import Object as GriffeObject

from .protocols import BundleProtocol, FilterProtocol, ProcessorProtocol


class PluginError(Exception):
    """Base exception for plugin-related errors."""


class PluginLoadError(PluginError):
    """Exception raised when a plugin cannot be loaded."""


class PluginManager:
    """Manages plugin discovery, loading, and execution."""

    def __init__(self) -> None:
        """Initialize the plugin manager."""
        self._processors: Dict[str, ProcessorProtocol] = {}
        self._filters: Dict[str, FilterProtocol] = {}
        self._bundles: Dict[str, BundleProtocol] = {}
        self._loaded = False

    def load_plugins(self) -> None:
        """Discover and load all available plugins via entry points."""
        if self._loaded:
            return

        # Load processors
        self._load_entry_points("griffonner.processors", self._processors)

        # Load filters
        self._load_entry_points("griffonner.filters", self._filters)

        # Load bundles
        bundles: Dict[str, BundleProtocol] = {}
        self._load_entry_points("griffonner.bundles", bundles)

        # Process bundles to extract their components
        for bundle_name, bundle in bundles.items():
            self._bundles[bundle_name] = bundle

            # Add bundle processors
            for proc_name, processor in bundle.get_processors().items():
                full_name = f"{bundle_name}.{proc_name}"
                self._processors[full_name] = processor

            # Add bundle filters
            for filter_name, filter_func in bundle.get_filters().items():
                full_name = f"{bundle_name}.{filter_name}"
                self._filters[full_name] = filter_func

        self._loaded = True

    def _load_entry_points(self, group: str, target_dict: Dict[str, Any]) -> None:
        """Load plugins from entry points into target dictionary.

        Args:
            group: Entry point group name
            target_dict: Dictionary to populate with loaded plugins
        """
        # Get all entry points (Python 3.9 compatible)
        all_entry_points = importlib.metadata.entry_points()

        # Get entry points for the specific group
        if hasattr(all_entry_points, "select"):
            # Python 3.10+ style
            entry_points = all_entry_points.select(group=group)
        elif hasattr(all_entry_points, "get"):
            # Python 3.9 style - entry_points is a dict
            entry_points = all_entry_points.get(group, [])
        else:
            # Handle other cases (like mocks that return lists)
            entry_points = []

        for entry_point in entry_points:
            try:
                plugin = entry_point.load()
                target_dict[entry_point.name] = plugin
            except Exception as e:
                raise PluginLoadError(
                    f"Failed to load plugin '{entry_point.name}' "
                    f"from group '{group}': {e}"
                ) from e

    def get_processors(self) -> Dict[str, ProcessorProtocol]:
        """Get all available processors.

        Returns:
            Dictionary mapping processor names to processor instances
        """
        self.load_plugins()
        return self._processors.copy()

    def get_filters(self) -> Dict[str, FilterProtocol]:
        """Get all available filters.

        Returns:
            Dictionary mapping filter names to filter functions
        """
        self.load_plugins()
        return self._filters.copy()

    def get_bundles(self) -> Dict[str, BundleProtocol]:
        """Get all available bundles.

        Returns:
            Dictionary mapping bundle names to bundle instances
        """
        self.load_plugins()
        return self._bundles.copy()

    def process_griffe_object(
        self,
        griffe_obj: Union[GriffeObject, Alias],
        context: Dict[str, Any],
        processor_names: Optional[List[str]] = None,
    ) -> tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        """Process a Griffe object through available processors.

        Args:
            griffe_obj: The Griffe object to process
            context: The template context dictionary
            processor_names: Optional list of processor names to use.
                            If None, uses all available processors.

        Returns:
            Tuple of (processed_griffe_obj, updated_context)
        """
        self.load_plugins()

        # Determine which processors to use
        if processor_names is None:
            processors = list(self._processors.values())
        else:
            processors = []
            for name in processor_names:
                if name in self._processors:
                    processors.append(self._processors[name])
                else:
                    raise PluginError(f"Processor '{name}' not found")

        # Sort processors by priority (lower priority runs first)
        processors.sort(key=lambda p: getattr(p, "priority", 100))

        # Run processors in sequence
        current_obj = griffe_obj
        current_context = context.copy()

        for processor in processors:
            try:
                current_obj, current_context = processor.process(
                    current_obj, current_context
                )
            except Exception as e:
                processor_name = getattr(processor, "name", "unknown")
                raise PluginError(f"Processor '{processor_name}' failed: {e}") from e

        return current_obj, current_context

    def list_plugins(self) -> Dict[str, List[str]]:
        """List all available plugins by category.

        Returns:
            Dictionary with 'processors', 'filters', and 'bundles' keys
        """
        self.load_plugins()
        return {
            "processors": list(self._processors.keys()),
            "filters": list(self._filters.keys()),
            "bundles": list(self._bundles.keys()),
        }

    def get_bundle_info(self, bundle_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific bundle.

        Args:
            bundle_name: Name of the bundle

        Returns:
            Bundle information dictionary or None if not found
        """
        self.load_plugins()
        bundle = self._bundles.get(bundle_name)
        if not bundle:
            return None

        return {
            "name": bundle.name,
            "version": bundle.version,
            "description": bundle.description,
            "processors": list(bundle.get_processors().keys()),
            "filters": list(bundle.get_filters().keys()),
            "template_paths": bundle.get_template_paths(),
        }
