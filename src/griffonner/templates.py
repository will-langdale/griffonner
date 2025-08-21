"""Template discovery and loading for Griffonner."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2


class TemplateError(Exception):
    """Base exception for template-related errors."""


class TemplateNotFoundError(TemplateError):
    """Exception raised when a template cannot be found."""


class TemplateValidationError(TemplateError):
    """Exception raised when a template fails validation."""


class TemplateLoader:
    """Handles template discovery and loading."""

    def __init__(self, template_dirs: Optional[List[Path]] = None) -> None:
        """Initialize the template loader.

        Args:
            template_dirs: Directories to search for templates
        """
        if template_dirs is None:
            template_dirs = []

        # Add built-in template directory (from the package)
        package_templates = Path(__file__).parent.parent.parent / "templates"

        # Add default template search paths
        default_dirs = [
            Path.cwd() / "docs" / "templates",
            Path.cwd() / "templates",
            package_templates,  # Built-in templates
        ]

        self.template_dirs = template_dirs + default_dirs

        # Create Jinja2 environment with FileSystemLoader
        existing_dirs = [str(d) for d in self.template_dirs if d.exists()]
        loader = jinja2.FileSystemLoader(existing_dirs)
        self.env = jinja2.Environment(
            loader=loader,
            autoescape=False,  # We're generating docs, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def load_template(self, template_path: str) -> jinja2.Template:
        """Load a template by path.

        Args:
            template_path: Relative path to template

        Returns:
            Loaded Jinja2 template

        Raises:
            TemplateNotFoundError: If template cannot be found
        """
        try:
            return self.env.get_template(template_path)
        except jinja2.TemplateNotFound as e:
            # Provide helpful suggestions when template is not found
            suggestions = self.suggest_template(template_path)
            error_msg = f"Template not found: {template_path}"

            if suggestions:
                error_msg += "\n\nDid you mean one of these?\n"
                for suggestion in suggestions:
                    error_msg += f"  - {suggestion}\n"

            # Show available template sets
            template_sets = self.get_available_template_sets()
            if template_sets:
                error_msg += "\nAvailable template sets:\n"
                for template_set in template_sets:
                    error_msg += f"  - {template_set}/\n"

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
        try:
            template = self.load_template(template_path)
            return template.render(**context)
        except jinja2.TemplateError as e:
            raise TemplateError(f"Template rendering failed: {e}") from e

    def find_templates(self, pattern: str = "**/*.jinja2") -> List[Path]:
        """Find all templates matching a pattern.

        Args:
            pattern: Glob pattern to match templates

        Returns:
            List of template paths relative to search directories
        """
        templates = []

        for template_dir in self.template_dirs:
            if template_dir.exists():
                for template_path in template_dir.glob(pattern):
                    if template_path.is_file():
                        # Make path relative to template directory
                        relative_path = template_path.relative_to(template_dir)
                        templates.append(relative_path)

        return sorted(set(templates))  # Remove duplicates and sort

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
        try:
            template = self.load_template(template_path)
            # Try to parse the template to check for syntax errors
            template.new_context()
        except jinja2.TemplateSyntaxError as e:
            msg = f"Template syntax error in {template_path}: {e}"
            raise TemplateValidationError(msg) from e
        except jinja2.TemplateError as e:
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
