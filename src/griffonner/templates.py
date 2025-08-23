"""Template discovery and loading for Griffonner."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .plugins.manager import PluginManager

import jinja2

logger = logging.getLogger("griffonner.templates")


class TemplateError(Exception):
    """Base exception for template-related errors."""


class TemplateNotFoundError(TemplateError):
    """Exception raised when a template cannot be found."""


class TemplateValidationError(TemplateError):
    """Exception raised when a template fails validation."""


class TemplateLoader:
    """Handles template discovery and loading."""

    def __init__(
        self,
        template_dirs: Optional[List[Path]] = None,
        plugin_manager: Optional["PluginManager"] = None,
    ) -> None:
        """Initialise the template loader.

        Args:
            template_dirs: Directories to search for templates
            plugin_manager: Optional plugin manager for custom filters
        """
        if template_dirs is None:
            template_dirs = []

        logger.info("Initialising TemplateLoader")
        logger.info(f"Template directories provided: {template_dirs}")

        # Add built-in template directory (from the package)
        package_templates = Path(__file__).parent.parent.parent / "templates"
        logger.info(f"Package templates directory: {package_templates}")

        # Add default template search paths
        default_dirs = [
            Path.cwd() / "docs" / "templates",
            Path.cwd() / "templates",
            package_templates,  # Built-in templates
        ]

        logger.info(f"Default template directories: {default_dirs}")

        self.template_dirs = template_dirs + default_dirs
        logger.info(f"Final template search paths: {self.template_dirs}")

        # Create Jinja2 environment with FileSystemLoader
        existing_dirs = [str(d) for d in self.template_dirs if d.exists()]
        non_existing_dirs = [str(d) for d in self.template_dirs if not d.exists()]

        logger.info(f"Existing template directories: {existing_dirs}")
        if non_existing_dirs:
            skipped_dirs = non_existing_dirs
            logger.info(f"Non-existing template directories (skipped): {skipped_dirs}")

        loader = jinja2.FileSystemLoader(existing_dirs)
        self.env = jinja2.Environment(
            loader=loader,
            autoescape=False,  # We're generating docs, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Register custom filters from plugin manager
        if plugin_manager:
            custom_filters = plugin_manager.get_filters()
            filter_count = len(custom_filters)
            logger.info(f"Registering {filter_count} custom filters from plugins")
            for filter_name, filter_func in custom_filters.items():
                self.env.filters[filter_name] = filter_func
                logger.info(f"Registered custom filter: {filter_name}")
        else:
            logger.info("No plugin manager provided, using default Jinja2 filters only")

    def load_template(self, template_path: str) -> jinja2.Template:
        """Load a template by path.

        Args:
            template_path: Relative path to template

        Returns:
            Loaded Jinja2 template

        Raises:
            TemplateNotFoundError: If template cannot be found
        """
        logger.info(f"Loading template: {template_path}")

        try:
            template = self.env.get_template(template_path)
            logger.info(f"Successfully loaded template: {template_path}")
            return template
        except jinja2.TemplateNotFound as e:
            logger.error(f"Template not found: {template_path}")

            # Provide helpful suggestions when template is not found
            suggestions = self.suggest_template(template_path)

            error_parts = [f"Template not found: {template_path}"]

            if suggestions:
                logger.info(f"Found {len(suggestions)} template suggestions")
                error_parts.append("\nDid you mean one of these?")
                for suggestion in suggestions:
                    error_parts.append(f"  - {suggestion}")

            # Show available template sets
            template_sets = self.get_available_template_sets()
            if template_sets:
                logger.info(f"Available template sets: {template_sets}")
                error_parts.append("\nAvailable template sets:")
                for template_set in template_sets:
                    error_parts.append(f"  - {template_set}/")

            error_msg = "\n".join(error_parts)
            raise TemplateNotFoundError(error_msg) from e

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """Render a template with the given context.

        Args:
            template_path: Relative path to template
            context: Template context variables

        Returns:
            Rendered template content

        Raises:
            TemplateNotFoundError: If template cannot be found
            TemplateError: If template rendering fails
        """
        logger.info(f"Rendering template: {template_path}")
        logger.info(f"Context keys: {list(context.keys())}")

        try:
            template = self.load_template(template_path)
            rendered = template.render(**context)
            char_count = len(rendered)
            logger.info(f"Rendered template: {template_path} ({char_count} characters)")
            return rendered
        except jinja2.TemplateError as e:
            logger.exception(f"Template rendering failed for {template_path}")
            raise TemplateError(f"Template rendering failed: {e}") from e

    def find_templates(self, pattern: str = "**/*.jinja2") -> List[Path]:
        """Find all templates matching a pattern.

        Args:
            pattern: Glob pattern to match templates

        Returns:
            List of template paths relative to search directories
        """
        logger.info(f"Searching for templates with pattern: {pattern}")
        templates = []

        for template_dir in self.template_dirs:
            if template_dir.exists():
                logger.info(f"Searching in directory: {template_dir}")
                dir_templates = []
                for template_path in template_dir.glob(pattern):
                    if template_path.is_file():
                        # Make path relative to template directory
                        relative_path = template_path.relative_to(template_dir)
                        templates.append(relative_path)
                        dir_templates.append(relative_path)

                logger.info(f"Found {len(dir_templates)} templates in {template_dir}")
            else:
                logger.info(f"Directory does not exist: {template_dir}")

        unique_templates = sorted(set(templates))  # Remove duplicates and sort
        logger.info(f"Total unique templates found: {len(unique_templates)}")
        return unique_templates

    def find_default_template(
        self, object_kind: str, language: str = "python"
    ) -> Optional[str]:
        """Find the default template for a given object kind.

        Args:
            object_kind: Type of object (module, class, function)
            language: Programming language (default: python)

        Returns:
            Template path if found, None otherwise
        """
        template_path = f"{language}/default/{object_kind}.md.jinja2"

        # Check if template exists in any of the template directories
        for template_dir in self.template_dirs:
            if template_dir.exists():
                full_path = template_dir / template_path
                if full_path.exists():
                    return template_path

        return None

    def validate_template(self, template_path: str) -> None:
        """Validate a template for syntax errors.

        Args:
            template_path: Relative path to template

        Raises:
            TemplateValidationError: If template has syntax errors
            TemplateNotFoundError: If template cannot be found
        """
        logger.info(f"Validating template: {template_path}")

        try:
            template = self.load_template(template_path)
            # Try to parse the template to check for syntax errors
            template.new_context()
            logger.info(f"Template validation successful: {template_path}")
        except jinja2.TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {template_path}: {e}")
            msg = f"Template syntax error in {template_path}: {e}"
            raise TemplateValidationError(msg) from e
        except jinja2.TemplateError as e:
            logger.error(f"Template validation failed for {template_path}: {e}")
            msg = f"Template validation failed for {template_path}: {e}"
            raise TemplateValidationError(msg) from e

    def get_available_template_sets(self) -> List[str]:
        """Get list of available template sets.

        Returns:
            List of template set paths (e.g., ['python/default', 'python/custom'])
        """
        template_sets = set()

        for template_dir in self.template_dirs:
            if template_dir.exists():
                # Look for language/style directories
                for lang_dir in template_dir.iterdir():
                    if lang_dir.is_dir():
                        for style_dir in lang_dir.iterdir():
                            if style_dir.is_dir():
                                template_set = f"{lang_dir.name}/{style_dir.name}"
                                template_sets.add(template_set)

        return sorted(template_sets)

    def suggest_template(self, template_path: str) -> List[str]:
        """Suggest alternative templates when a template is not found.

        Args:
            template_path: The template path that was not found

        Returns:
            List of suggested template paths
        """
        suggestions = []
        all_templates = self.find_templates()

        # Extract the filename from the requested path
        requested_filename = Path(template_path).name
        requested_dir = str(Path(template_path).parent)

        # Find templates with similar names or in similar directories
        for template in all_templates:
            template_str = str(template)
            template_dir = str(template.parent)

            # Exact filename match
            if template.name == requested_filename:
                suggestions.append(template_str)
            # Filename contains requested name
            elif requested_filename in template.name:
                suggestions.append(template_str)
            # Same directory structure
            elif requested_dir in template_dir:
                suggestions.append(template_str)
            # Similar directory names
            elif template_dir.replace("/", "_") in requested_dir.replace("/", "_"):
                suggestions.append(template_str)

        return suggestions[:5]  # Limit to 5 suggestions
