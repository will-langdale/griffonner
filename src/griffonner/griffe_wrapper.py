"""Minimal Griffe integration for Griffonner."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import griffe
from griffe import Alias
from griffe import Object as GriffeObject

logger = logging.getLogger("griffonner.griffe")


class GriffeError(Exception):
    """Base exception for Griffe-related errors."""


class ModuleLoadError(GriffeError):
    """Exception raised when a module cannot be loaded."""


def load_griffe_object(
    target: str,
    search_paths: Optional[List[Path]] = None,
    griffe_options: Optional[Dict[str, Any]] = None,
) -> Union[GriffeObject, Alias]:
    """Load a Griffe object from module name.

    Args:
        target: Module name (e.g., 'mypackage.utils', 'os', 'pathlib')
        search_paths: Additional paths to search for modules
        griffe_options: Options to pass to Griffe loader

    Returns:
        Raw Griffe object

    Raises:
        ModuleLoadError: If target cannot be loaded
    """
    if search_paths is None:
        search_paths = []
    if griffe_options is None:
        griffe_options = {}

    logger.info(f"Loading Griffe object for target: {target}")
    logger.info(f"Search paths provided: {search_paths}")
    logger.info(f"Griffe options: {griffe_options}")

    # Add current working directory and src to search paths
    default_paths = [Path.cwd(), Path.cwd() / "src"]
    all_search_paths = search_paths + default_paths

    logger.info(f"Final search paths: {all_search_paths}")

    # Add to Python path for imports
    python_paths_added = []
    for path in all_search_paths:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))
            python_paths_added.append(str(path))
            logger.info(f"Added to sys.path: {path}")
        elif not path.exists():
            logger.info(f"Search path does not exist: {path}")

    logger.info(f"Added {len(python_paths_added)} paths to sys.path")

    try:
        logger.info("Creating GriffeLoader instance")
        loader = griffe.GriffeLoader(
            search_paths=all_search_paths,
            **griffe_options,
        )

        logger.info(f"Loading target '{target}' with Griffe")
        griffe_obj = loader.load(target)

        if griffe_obj is None:
            logger.error(f"Griffe returned None for target '{target}'")
            raise ModuleLoadError(f"Target '{target}' not found")

        logger.info(f"Successfully loaded Griffe object: {type(griffe_obj).__name__}")
        logger.info(f"Object name: {getattr(griffe_obj, 'name', 'unknown')}")
        logger.info(f"Object kind: {getattr(griffe_obj, 'kind', 'unknown')}")

        return griffe_obj

    except griffe.LoadingError as e:
        logger.error(f"Griffe LoadingError for '{target}': {e}")
        raise ModuleLoadError(f"Target '{target}' not found: {e}") from e
    except Exception as e:
        logger.exception(f"Unexpected error loading target '{target}'")
        raise ModuleLoadError(f"Failed to load target '{target}': {e}") from e
