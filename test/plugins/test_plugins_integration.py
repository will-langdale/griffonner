"""Integration tests for plugin system with core generation."""

from pathlib import Path
from typing import Any, Dict, Tuple, Union
from unittest.mock import Mock, patch

from griffe import Alias
from griffe import Object as GriffeObject

from griffonner.frontmatter import FrontmatterConfig, OutputItem, ProcessorConfig
from griffonner.plugins.base import BaseProcessor, SimpleProcessor
from griffonner.plugins.manager import PluginManager
from griffonner.templates import TemplateLoader


class TestProcessor(BaseProcessor):
    """Test processor that adds metadata to context."""

    @property
    def name(self) -> str:
        return "test_processor"

    def process(
        self, griffe_obj: Union[GriffeObject, Alias], context: Dict[str, Any]
    ) -> Tuple[Union[GriffeObject, Alias], Dict[str, Any]]:
        # Add some test metadata
        context["test_metadata"] = {
            "processed": True,
            "processor": self.name,
            "object_name": getattr(griffe_obj, "name", "unknown"),
        }
        return griffe_obj, context


def uppercase_filter_func(value: str) -> str:
    """Filter function that converts to uppercase."""
    return value.upper()


class TestPluginIntegration:
    """Integration tests for plugin system with core components."""

    def test_template_loader_with_custom_filters(self, tmp_path):
        """Test that TemplateLoader correctly registers custom filters."""
        # Create a template that uses custom filter
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        template_file = template_dir / "test.jinja2"
        template_file.write_text("{{ value | test_filter }}")

        # Create plugin manager with custom filter
        plugin_manager = PluginManager()
        plugin_manager._filters = {"test_filter": uppercase_filter_func}
        plugin_manager._loaded = True

        # Create template loader with plugin manager
        loader = TemplateLoader([template_dir], plugin_manager)

        # Test that filter is available
        result = loader.render_template("test.jinja2", {"value": "hello"})
        assert result == "HELLO"

    @patch("griffonner.core.load_griffe_object")
    def test_core_generation_with_processors(self, mock_load_griffe):
        """Test that core generation correctly uses processors."""
        from griffonner.core import generate_file
        from griffonner.frontmatter import ParsedFile

        # Mock Griffe object
        mock_griffe_obj = Mock()
        mock_griffe_obj.name = "test_module"
        mock_load_griffe.return_value = mock_griffe_obj

        # Create plugin manager with test processor
        plugin_manager = PluginManager()
        test_processor = TestProcessor()
        plugin_manager._processors = {"test_processor": test_processor}
        plugin_manager._loaded = True

        # Mock parsed file with processor config
        processor_config = ProcessorConfig(enabled=["test_processor"])
        frontmatter = FrontmatterConfig(
            template="test.jinja2",
            output=[OutputItem(filename="output.md", griffe_target="test.module")],
            processors=processor_config,
        )

        with patch("griffonner.core.parse_frontmatter_file") as mock_parse:
            mock_parse.return_value = ParsedFile(
                frontmatter=frontmatter,
                content="Test content",
                source_path=Path("test.md"),
            )

            with patch("griffonner.core.TemplateLoader") as mock_template_loader:
                mock_template_instance = Mock()
                mock_template_instance.render_template.return_value = "Rendered content"
                mock_template_loader.return_value = mock_template_instance

                with patch("pathlib.Path.write_text") as mock_write:
                    mock_write.return_value = None

                    with patch("pathlib.Path.mkdir"):
                        # Run generation
                        generate_file(
                            Path("test.md"),
                            Path("."),
                            Path("output"),
                            plugin_manager=plugin_manager,
                        )

                        # Verify template loader was called with plugin manager
                        mock_template_loader.assert_called_once()
                        call_args = mock_template_loader.call_args
                        # Second argument should be plugin_manager
                        assert call_args[0][1] is plugin_manager

                        # Verify render_template was called
                        mock_template_instance.render_template.assert_called_once()
                        render_call_args = (
                            mock_template_instance.render_template.call_args
                        )

                        # Check that context includes processor metadata
                        # render_template is called with (template_path, context)
                        # Second positional argument is context
                        context = render_call_args[0][1]
                        assert "test_metadata" in context
                        assert context["test_metadata"]["processed"] is True
                        assert context["test_metadata"]["processor"] == "test_processor"

    def test_frontmatter_processor_config_parsing(self):
        """Test that frontmatter correctly parses processor configuration."""
        from griffonner.frontmatter import (
            FrontmatterConfig,
        )

        # Test with enabled processors
        config_data = {
            "template": "test.jinja2",
            "output": [{"filename": "test.md", "griffe_target": "test.module"}],
            "processors": {
                "enabled": ["proc1", "proc2"],
                "config": {"setting1": "value1"},
            },
        }

        config = FrontmatterConfig.model_validate(config_data)

        assert config.processors is not None
        assert config.processors.enabled == ["proc1", "proc2"]
        assert config.processors.disabled == []
        assert config.processors.config == {"setting1": "value1"}

        # Test with disabled processors
        config_data["processors"] = {"disabled": ["proc3", "proc4"]}

        config = FrontmatterConfig.model_validate(config_data)

        assert config.processors is not None
        assert config.processors.enabled == []
        assert config.processors.disabled == ["proc3", "proc4"]
        assert config.processors.config == {}

    def test_processor_priority_ordering(self):
        """Test that processors are executed in priority order."""
        manager = PluginManager()

        # Create processors with different priorities
        early_processor = SimpleProcessor(
            "early",
            lambda obj, ctx: (obj, {**ctx, "order": ctx.get("order", []) + ["early"]}),
            priority=50,
        )

        late_processor = SimpleProcessor(
            "late",
            lambda obj, ctx: (obj, {**ctx, "order": ctx.get("order", []) + ["late"]}),
            priority=150,
        )

        default_processor = SimpleProcessor(
            "default",
            lambda obj, ctx: (
                obj,
                {**ctx, "order": ctx.get("order", []) + ["default"]},
            ),
            priority=100,
        )

        manager._processors = {
            "late": late_processor,
            "early": early_processor,
            "default": default_processor,
        }
        manager._loaded = True

        obj = Mock()
        context = {}

        result_obj, result_context = manager.process_griffe_object(obj, context)

        # Should be executed in priority order: early (50), default (100), late (150)
        assert result_context["order"] == ["early", "default", "late"]
