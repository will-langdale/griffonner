"""Protocol definitions for Griffonner plugins."""

from typing import Any, Dict, Protocol, Tuple, Union

from griffe import Alias
from griffe import Object as GriffeObject


class ProcessorProtocol(Protocol):
    """Protocol for processors that transform Griffe objects before templating.

    Processors are middleware components that can modify the Griffe object
    and/or template context before the template rendering phase.
    """

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
        ...

    @property
    def name(self) -> str:
        """Name of the processor for identification."""
        ...

    @property
    def priority(self) -> int:
        """Priority for processor execution order (lower = earlier).

        Default processors run at priority 100.
        Use lower values to run before defaults, higher to run after.
        """
        ...


class FilterProtocol(Protocol):
    """Protocol for custom Jinja2 template filters.

    Filters are functions that transform data in templates using the pipe syntax:
    {{ value | filter_name }}
    """

    def __call__(self, value: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute the filter on a value.

        Args:
            value: The input value to filter
            *args: Positional arguments for the filter
            **kwargs: Keyword arguments for the filter

        Returns:
            The filtered value
        """
        ...


class BundleProtocol(Protocol):
    """Protocol for plugin bundles that group templates, processors, and filters.

    Bundles allow packaging related functionality together, like a complete
    GitLab wiki documentation system with custom processors and filters.
    """

    @property
    def name(self) -> str:
        """Name of the bundle for identification."""
        ...

    @property
    def version(self) -> str:
        """Version of the bundle."""
        ...

    @property
    def description(self) -> str:
        """Description of what this bundle provides."""
        ...

    def get_processors(self) -> Dict[str, ProcessorProtocol]:
        """Get processors provided by this bundle.

        Returns:
            Dictionary mapping processor names to processor instances
        """
        ...

    def get_filters(self) -> Dict[str, FilterProtocol]:
        """Get filters provided by this bundle.

        Returns:
            Dictionary mapping filter names to filter functions
        """
        ...

    def get_template_paths(self) -> list[str]:
        """Get template directory paths provided by this bundle.

        Returns:
            List of template directory paths relative to the bundle
        """
        ...
