"""Base classes for Griffonner plugins."""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Tuple, Union

from griffe import Alias
from griffe import Object as GriffeObject

from .protocols import FilterProtocol, ProcessorProtocol


class BaseProcessor(ABC):
    """Base class for processors that implement ProcessorProtocol."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the processor for identification."""
        pass

    @property
    def priority(self) -> int:
        """Priority for processor execution order (lower = earlier).

        Default processors run at priority 100.
        Use lower values to run before defaults, higher to run after.
        """
        return 100

    @abstractmethod
    def process(
        self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
    ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        """Process a Griffe object and template context.

        Args:
            griffe_obj: The Griffe object to process
            context: The template context dictionary

        Returns:
            Tuple of (processed_griffe_obj, updated_context)
        """
        pass


class BaseBundle(ABC):
    """Base class for plugin bundles."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the bundle for identification."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Version of the bundle."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this bundle provides."""
        pass

    def get_processors(self) -> Dict[str, ProcessorProtocol]:
        """Get processors provided by this bundle.

        Returns:
            Dictionary mapping processor names to processor instances
        """
        return {}

    def get_filters(self) -> Dict[str, FilterProtocol]:
        """Get filters provided by this bundle.

        Returns:
            Dictionary mapping filter names to filter functions
        """
        return {}

    def get_template_paths(self) -> List[str]:
        """Get template directory paths provided by this bundle.

        Returns:
            List of template directory paths relative to the bundle
        """
        return []


class SimpleProcessor(BaseProcessor):
    """Simple processor implementation for common use cases."""

    def __init__(
        self,
        name: str,
        process_func: Callable[
            [Union[GriffeObject, Alias], Dict[str, Any]],
            Tuple[Union[GriffeObject, Alias], Dict[str, Any]],
        ],
        priority: int = 100,
    ) -> None:
        """Initialise a simple processor.

        Args:
            name: Name of the processor
            process_func: Function that processes (griffe_obj, context) and returns
                         (griffe_obj, context)
            priority: Execution priority
        """
        self._name = name
        self._process_func = process_func
        self._priority = priority

    @property
    def name(self) -> str:
        """Name of the processor for identification."""
        return self._name

    @property
    def priority(self) -> int:
        """Priority for processor execution order."""
        return self._priority

    def process(
        self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
    ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        """Process using the provided function."""
        return self._process_func(griffe_obj, context)
