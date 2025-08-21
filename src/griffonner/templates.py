"""Template discovery and loading for Griffonner."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2


class TemplateError(Exception):
    """Base exception for template-related errors."""


class TemplateNotFoundError(TemplateError):
    """Exception raised when a template cannot be found."""


class TemplateLoader:
    """Handles template discovery and loading."""

    def __init__(self, template_dirs: Optional[List[Path]] = None) -> None:
        """Initialize the template loader.

        Args:
            template_dirs: Directories to search for templates
        """
        if template_dirs is None:
            template_dirs = []

        # Add default template search paths
        default_dirs = [
            Path.cwd() / "docs" / "templates",
            Path.cwd() / "templates",
        ]

        self.template_dirs = template_dirs + default_dirs

        # Create Jinja2 environment with FileSystemLoader
        loader = jinja2.FileSystemLoader([str(d) for d in self.template_dirs])
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
            raise TemplateNotFoundError(f"Template not found: {template_path}") from e

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
