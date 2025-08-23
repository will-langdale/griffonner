"""Plugin manager for discovering and loading Griffonner plugins."""

import importlib.metadata
import logging
from typing import Any, Dict, List, Optional, Union

from griffe import Alias
from griffe import Object as GriffeObject

from .protocols import BundleProtocol, FilterProtocol, ProcessorProtocol

logger = logging.getLogger("griffonner.plugins")


class PluginError(Exception):
    """Base exception for plugin-related errors."""


class PluginLoadError(PluginError):
    """Exception raised when a plugin cannot be loaded."""


class PluginManager:
    """Manages plugin discovery, loading, and execution."""

    def __init__(self) -> None:
        """Initialise the plugin manager."""
        self._processors: Dict[str, ProcessorProtocol] = {}
        self._filters: Dict[str, FilterProtocol] = {}
        self._bundles: Dict[str, BundleProtocol] = {}
        self._loaded = False

    def load_plugins(self) -> None:
        """Discover and load all available plugins via entry points."""
        if self._loaded:
            logger.info("Plugins already loaded, skipping")
            return

        logger.info("Starting plugin discovery and loading")

        # Load processors
        logger.info("Loading processors from entry points")
        self._load_entry_points("griffonner.processors", self._processors)
        logger.info(f"Loaded {len(self._processors)} processors")

        # Load filters
        logger.info("Loading filters from entry points")
        self._load_entry_points("griffonner.filters", self._filters)
        logger.info(f"Loaded {len(self._filters)} filters")

        # Load bundles
        logger.info("Loading bundles from entry points")
        bundles: Dict[str, BundleProtocol] = {}
        self._load_entry_points("griffonner.bundles", bundles)
        logger.info(f"Loaded {len(bundles)} bundles")

        # Process bundles to extract their components
        logger.info("Processing bundles to extract components")
        for bundle_name, bundle in bundles.items():
            logger.info(f"Processing bundle: {bundle_name}")
            self._bundles[bundle_name] = bundle

            # Add bundle processors
            bundle_processors = bundle.get_processors()
            processor_count = len(bundle_processors)
            logger.info(f"Bundle {bundle_name} provides {processor_count} processors")
            for proc_name, processor in bundle_processors.items():
                full_name = f"{bundle_name}.{proc_name}"
                self._processors[full_name] = processor
                logger.info(f"Registered processor: {full_name}")

            # Add bundle filters
            bundle_filters = bundle.get_filters()
            logger.info(f"Bundle {bundle_name} provides {len(bundle_filters)} filters")
            for filter_name, filter_func in bundle_filters.items():
                full_name = f"{bundle_name}.{filter_name}"
                self._filters[full_name] = filter_func
                logger.info(f"Registered filter: {full_name}")

        self._loaded = True
        proc_count = len(self._processors)
        filter_count = len(self._filters)
        bundle_count = len(self._bundles)
        logger.info(
            f"Plugin loading: {proc_count} processors, {filter_count} filters, "
            f"{bundle_count} bundles"
        )

    def _load_entry_points(self, group: str, target_dict: Dict[str, Any]) -> None:
        """Load plugins from entry points into target dictionary.

        Args:
            group: Entry point group name
            target_dict: Dictionary to populate with loaded plugins
        """
        logger.info(f"Discovering entry points for group: {group}")

        # Get all entry points (Python 3.9 compatible)
        all_entry_points = importlib.metadata.entry_points()

        # Get entry points for the specific group
        if hasattr(all_entry_points, "select"):
            # Python 3.10+ style
            logger.info("Using Python 3.10+ entry_points.select() method")
            entry_points = all_entry_points.select(group=group)
        elif hasattr(all_entry_points, "get"):
            # Python 3.9 style - entry_points is a dict
            logger.info("Using Python 3.9 entry_points.get() method")
            entry_points = all_entry_points.get(group, [])
        else:
            # Handle other cases (like mocks that return lists)
            logger.warning("Unknown entry_points type, using empty list")
            entry_points = []

        entry_points_list = list(entry_points)
        logger.info(f"Found {len(entry_points_list)} entry points for group {group}")

        for entry_point in entry_points_list:
            ep_name, ep_value = entry_point.name, entry_point.value
            logger.info(f"Loading entry point: {ep_name} -> {ep_value}")
            try:
                plugin = entry_point.load()
                target_dict[entry_point.name] = plugin
                logger.info(f"Successfully loaded plugin: {entry_point.name}")
            except Exception as e:
                logger.exception(f"Failed to load plugin: {entry_point.name}")
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

        obj_name = getattr(griffe_obj, "name", "unknown")
        logger.info(f"Processing Griffe object: {obj_name}")
        logger.info(f"Object type: {type(griffe_obj).__name__}")

        # Determine which processors to use
        if processor_names is None:
            processors = list(self._processors.values())
            logger.info(f"Using all available processors: {len(processors)}")
        else:
            logger.info(f"Using specified processors: {processor_names}")
            processors = []
            for name in processor_names:
                if name in self._processors:
                    processors.append(self._processors[name])
                    logger.info(f"Found processor: {name}")
                else:
                    logger.error(f"Processor not found: {name}")
                    raise PluginError(f"Processor '{name}' not found")

        # Sort processors by priority (lower priority runs first)
        processors.sort(key=lambda p: getattr(p, "priority", 100))

        processor_info = [
            (getattr(p, "name", "unknown"), getattr(p, "priority", 100))
            for p in processors
        ]
        logger.info(f"Processor execution order: {processor_info}")

        # Run processors in sequence
        current_obj = griffe_obj
        current_context = context.copy()

        for i, processor in enumerate(processors):
            processor_name = getattr(processor, "name", "unknown")
            logger.info(f"Running processor {i+1}/{len(processors)}: {processor_name}")

            try:
                current_obj, current_context = processor.process(
                    current_obj, current_context
                )
                logger.info(f"Processor {processor_name} completed successfully")
            except Exception as e:
                logger.exception(f"Processor {processor_name} failed")
                raise PluginError(f"Processor '{processor_name}' failed: {e}") from e

        logger.info(f"All {len(processors)} processors completed successfully")
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
