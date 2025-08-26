"""Tests for plugin base classes."""

from typing import Any, Dict, Tuple, Union

import pytest
from griffe import Alias
from griffe import Object as GriffeObject

from griffonner.plugins.base import BaseBundle, BaseProcessor, SimpleProcessor


class TestBaseProcessor:
    """Tests for BaseProcessor abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseProcessor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseProcessor()

    def test_concrete_implementation(self):
        """Test that a concrete implementation works correctly."""

        class ConcreteProcessor(BaseProcessor):
            @property
            def name(self) -> str:
                return "concrete"

            def process(
                self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
            ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
                # Add a marker to context
                context["processed_by"] = self.name
                return griffe_obj, context

        processor = ConcreteProcessor()
        assert processor.name == "concrete"
        assert processor.priority == 100  # Default priority

        # Test processing
        context = {"test": "value"}
        obj = object()  # Mock griffe object
        result_obj, result_context = processor.process(obj, context)

        assert result_obj is obj
        assert result_context["test"] == "value"
        assert result_context["processed_by"] == "concrete"

    def test_custom_priority(self):
        """Test processor with custom priority."""

        class HighPriorityProcessor(BaseProcessor):
            @property
            def name(self) -> str:
                return "high-priority"

            @property
            def priority(self) -> int:
                return 50

            def process(
                self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
            ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
                return griffe_obj, context

        processor = HighPriorityProcessor()
        assert processor.priority == 50


class TestBaseBundle:
    """Tests for BaseBundle abstract class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseBundle cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseBundle()

    def test_concrete_implementation(self):
        """Test that a concrete implementation works correctly."""

        class ConcreteBundle(BaseBundle):
            @property
            def name(self) -> str:
                return "test-bundle"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def description(self) -> str:
                return "Test bundle description"

        bundle = ConcreteBundle()
        assert bundle.name == "test-bundle"
        assert bundle.version == "1.0.0"
        assert bundle.description == "Test bundle description"

        # Test default implementations
        assert bundle.get_processors() == {}
        assert bundle.get_filters() == {}
        assert bundle.get_template_paths() == []

    def test_bundle_with_components(self):
        """Test bundle that provides processors and filters."""

        def test_filter(value):
            return str(value).upper()

        class TestProcessor(BaseProcessor):
            @property
            def name(self) -> str:
                return "test-proc"

            def process(self, griffe_obj, context):
                return griffe_obj, context

        class FullBundle(BaseBundle):
            @property
            def name(self) -> str:
                return "full-bundle"

            @property
            def version(self) -> str:
                return "2.0.0"

            @property
            def description(self) -> str:
                return "Full featured bundle"

            def get_processors(self):
                return {"test": TestProcessor()}

            def get_filters(self):
                return {"uppercase": test_filter}

            def get_template_paths(self):
                return ["templates/custom/"]

        bundle = FullBundle()
        processors = bundle.get_processors()
        filters = bundle.get_filters()
        template_paths = bundle.get_template_paths()

        assert "test" in processors
        assert isinstance(processors["test"], TestProcessor)
        assert "uppercase" in filters
        assert filters["uppercase"]("test") == "TEST"
        assert template_paths == ["templates/custom/"]


class TestSimpleProcessor:
    """Tests for SimpleProcessor utility class."""

    def test_simple_processor_creation(self):
        """Test creating a simple processor with a function."""

        def process_func(griffe_obj, context):
            context["simple"] = True
            return griffe_obj, context

        processor = SimpleProcessor("simple", process_func, priority=75)

        assert processor.name == "simple"
        assert processor.priority == 75

        # Test processing
        context = {}
        obj = object()
        result_obj, result_context = processor.process(obj, context)

        assert result_obj is obj
        assert result_context["simple"] is True

    def test_simple_processor_default_priority(self):
        """Test simple processor with default priority."""

        def process_func(griffe_obj, context):
            return griffe_obj, context

        processor = SimpleProcessor("default", process_func)
        assert processor.priority == 100
