"""Plugin manager for discovering and loading Griffonner plugins."""

import importlib
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

    def __init__(
        self,
        local_plugin_modules: Optional[List[str]] = None,
    ) -> None:
        """Initialise the plugin manager.

        Args:
            local_plugin_modules: Module names to import for local plugins
        """
        self._processors: Dict[str, ProcessorProtocol] = {}
        self._filters: Dict[str, FilterProtocol] = {}
        self._bundles: Dict[str, BundleProtocol] = {}
        self._loaded = False

        self.local_plugin_modules = local_plugin_modules or []

        logger.info(f"Local plugin modules: {self.local_plugin_modules}")

    def load_plugins(self) -> None:
        """Discover and load all plugins via entry points and local modules."""
        if self._loaded:
            logger.info("Plugins already loaded, skipping")
            return

        logger.info("Starting plugin discovery and loading")

        # Load processors from entry points
        logger.info("Loading processors from entry points")
        self._load_entry_points("griffonner.processors", self._processors)
        entry_point_processor_count = len(self._processors)
        logger.info(
            f"Loaded {entry_point_processor_count} processors from entry points"
        )

        # Load filters from entry points
        logger.info("Loading filters from entry points")
        self._load_entry_points("griffonner.filters", self._filters)
        entry_point_filter_count = len(self._filters)
        logger.info(f"Loaded {entry_point_filter_count} filters from entry points")

        # Load local plugins from specified modules
        logger.info("Loading local plugins from specified modules")
        local_processor_count, local_filter_count = self._load_local_plugin_modules()
        logger.info(f"Loaded {local_processor_count} local processors")
        logger.info(f"Loaded {local_filter_count} local filters")

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
        total_proc_count = len(self._processors)
        total_filter_count = len(self._filters)
        bundle_count = len(self._bundles)
        logger.info(
            f"Plugin loading complete: {total_proc_count} processors, "
            f"{total_filter_count} filters, {bundle_count} bundles"
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

    def _load_local_plugin_modules(self) -> tuple[int, int]:
        """Load plugins from specified local modules.

        Returns:
            Tuple of (processor_count, filter_count) loaded
        """
        processor_count = 0
        filter_count = 0

        for module_name in self.local_plugin_modules:
            logger.info(f"Loading local plugins from module: {module_name}")

            try:
                module = importlib.import_module(module_name)
                logger.info(f"Successfully imported module: {module_name}")

                # Extract filters and processors from the module
                module_processors = self._extract_processors_from_module(
                    module, module_name
                )
                module_filters = self._extract_filters_from_module(module, module_name)

                processor_count += len(module_processors)
                filter_count += len(module_filters)

                logger.info(
                    f"Module {module_name}: {len(module_processors)} processors, "
                    f"{len(module_filters)} filters"
                )

            except ImportError as e:
                logger.error(f"Failed to import module {module_name}: {e}")
                logger.warning(f"Skipping module {module_name}")
            except Exception as e:
                logger.exception(f"Unexpected error loading module {module_name}: {e}")
                logger.warning(f"Skipping module {module_name}")

        return processor_count, filter_count

    def _extract_filters_from_module(
        self, module: Any, module_name: str
    ) -> Dict[str, FilterProtocol]:
        """Extract filter functions from a module.

        Args:
            module: The imported module
            module_name: Name of the module for qualified names

        Returns:
            Dictionary of filter name to filter function
        """
        filters = {}

        for attr_name in dir(module):
            # Skip private attributes and imports
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)

            # Look for callable functions (not classes)
            if callable(attr) and not isinstance(attr, type):
                filters[attr_name] = attr
                logger.info(f"Found filter function: {attr_name}")

                # Register the filter with both simple and qualified names
                if attr_name not in self._filters:
                    self._filters[attr_name] = attr
                    logger.info(f"Registered filter: {attr_name}")
                else:
                    logger.warning(
                        f"Filter name conflict, skipping simple name: {attr_name}"
                    )

                # Always register qualified name
                qualified_name = f"{module_name}.{attr_name}"
                self._filters[qualified_name] = attr
                logger.info(f"Registered qualified filter: {qualified_name}")

        return filters

    def _extract_processors_from_module(
        self, module: Any, module_name: str
    ) -> Dict[str, ProcessorProtocol]:
        """Extract processor classes from a module.

        Args:
            module: The imported module
            module_name: Name of the module for qualified names

        Returns:
            Dictionary of processor name to processor instance
        """
        processors = {}

        for attr_name in dir(module):
            # Skip private attributes and imports
            if attr_name.startswith("_"):
                continue

            attr = getattr(module, attr_name)

            # Look for processor classes, but skip imported base classes
            if (
                isinstance(attr, type)
                and self._is_processor_class(attr)
                and self._is_defined_in_module(attr, module)
            ):
                logger.info(f"Found processor class: {attr_name}")

                try:
                    # Instantiate the processor
                    processor_instance = attr()

                    # Get processor name (from name property or derive from class name)
                    if hasattr(processor_instance, "name"):
                        processor_name = processor_instance.name
                    else:
                        # Convert CamelCase to snake_case
                        processor_name = self._class_name_to_snake_case(attr_name)

                    processors[processor_name] = processor_instance

                    # Register with both simple and qualified names
                    if processor_name not in self._processors:
                        self._processors[processor_name] = processor_instance
                        logger.info(f"Registered processor: {processor_name}")
                    else:
                        logger.warning(
                            f"Processor name conflict, skipping simple name: "
                            f"{processor_name}"
                        )

                    # Always register qualified name
                    qualified_name = f"{module_name}.{processor_name}"
                    self._processors[qualified_name] = processor_instance
                    logger.info(f"Registered qualified processor: {qualified_name}")

                except Exception as e:
                    logger.exception(
                        f"Failed to instantiate processor {attr_name}: {e}"
                    )
                    logger.warning(f"Skipping processor {attr_name}")

        return processors

    def _is_processor_class(self, cls: type) -> bool:
        """Check if a class implements ProcessorProtocol by duck typing.

        Args:
            cls: Class to check

        Returns:
            True if the class appears to implement ProcessorProtocol
        """
        # Check for required methods
        if not hasattr(cls, "process") or not callable(cls.process):
            return False

        # The name property can be either on the class or instance
        # We'll check after instantiation if needed
        return True

    def _is_defined_in_module(self, cls: type, module: Any) -> bool:
        """Check if a class is defined in the given module (not imported).

        Args:
            cls: Class to check
            module: Module to check against

        Returns:
            True if the class is defined in this module
        """
        # Check if the class's module matches the current module
        return hasattr(cls, "__module__") and cls.__module__ == module.__name__

    def _class_name_to_snake_case(self, class_name: str) -> str:
        """Convert CamelCase class name to snake_case.

        Args:
            class_name: Class name in CamelCase

        Returns:
            Class name in snake_case
        """
        import re

        # Insert underscore before uppercase letters (except first character)
        snake_case = re.sub(r"(?<!^)([A-Z])", r"_\1", class_name)
        return snake_case.lower()
