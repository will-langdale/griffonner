"""Minimal Griffe integration for Griffonner."""

import sys
from pathlib import Path
from typing import List, Optional, Union

import griffe
from griffe import Alias
from griffe import Object as GriffeObject


class GriffeError(Exception):
    """Base exception for Griffe-related errors."""


class ModuleLoadError(GriffeError):
    """Exception raised when a module cannot be loaded."""


def load_griffe_object(
    target: str, search_paths: Optional[List[Path]] = None
) -> Union[GriffeObject, Alias]:
    """Load a Griffe object from module name.

    Args:
        target: Module name (e.g., 'mypackage.utils', 'os', 'pathlib')
        search_paths: Additional paths to search for modules

    Returns:
        Raw Griffe object

    Raises:
        ModuleLoadError: If target cannot be loaded
    """
    if search_paths is None:
        search_paths = []

    # Add current working directory and src to search paths
    default_paths = [Path.cwd(), Path.cwd() / "src"]
    all_search_paths = search_paths + default_paths

    # Add to Python path for imports
    for path in all_search_paths:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))

    try:
        loader = griffe.GriffeLoader(
            search_paths=all_search_paths,
        )

        griffe_obj = loader.load(target)

        if griffe_obj is None:
            raise ModuleLoadError(f"Target '{target}' not found")

        return griffe_obj

    except griffe.LoadingError as e:
        raise ModuleLoadError(f"Target '{target}' not found: {e}") from e
    except Exception as e:
        raise ModuleLoadError(f"Failed to load target '{target}': {e}") from e
