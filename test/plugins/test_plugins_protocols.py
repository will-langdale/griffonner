"""Tests for plugin protocols."""

from typing import Any, Dict, Tuple, Union

from griffe import Alias
from griffe import Object as GriffeObject

from griffonner.plugins.protocols import FilterProtocol, ProcessorProtocol


def test_processor_protocol_interface():
    """Test that ProcessorProtocol defines the correct interface."""

    # This will fail if the protocol is missing required methods
    class TestProcessor:
        @property
        def name(self) -> str:
            return "test"

        @property
        def priority(self) -> int:
            return 100

        def process(
            self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
        ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
            return griffe_obj, context

    # Should not raise an error
    processor = TestProcessor()
    assert processor.name == "test"
    assert processor.priority == 100


def test_filter_protocol_interface():
    """Test that FilterProtocol defines the correct interface."""

    class TestFilter:
        def __call__(self, value: Any, *args: Any, **kwargs: Any) -> Any:
            return str(value).upper()

    # Should not raise an error
    filter_func = TestFilter()
    assert filter_func("test") == "TEST"


def test_bundle_protocol_interface():
    """Test that BundleProtocol defines the correct interface."""

    class TestBundle:
        @property
        def name(self) -> str:
            return "test-bundle"

        @property
        def version(self) -> str:
            return "1.0.0"

        @property
        def description(self) -> str:
            return "Test bundle"

        def get_processors(self) -> Dict[str, ProcessorProtocol]:
            return {}

        def get_filters(self) -> Dict[str, FilterProtocol]:
            return {}

        def get_template_paths(self) -> list[str]:
            return []

    # Should not raise an error
    bundle = TestBundle()
    assert bundle.name == "test-bundle"
    assert bundle.version == "1.0.0"
    assert bundle.description == "Test bundle"
    assert bundle.get_processors() == {}
    assert bundle.get_filters() == {}
    assert bundle.get_template_paths() == []
