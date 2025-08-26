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
    griffe_config: Optional[Dict[str, Any]] = None,
) -> Union[GriffeObject, Alias]:
    """Load a Griffe object using flexible configuration.

    Args:
        target: Module name (e.g., 'mypackage.utils', 'os', 'pathlib')
        search_paths: Additional paths to search for modules
        griffe_config: Griffe configuration with loader options and method calls

    Returns:
        Raw Griffe object

    Raises:
        ModuleLoadError: If target cannot be loaded
    """
    if search_paths is None:
        search_paths = []
    if griffe_config is None:
        griffe_config = {}

    logger.info(f"Loading Griffe object for target: {target}")
    logger.info(f"Search paths provided: {search_paths}")
    logger.info(f"Griffe config: {griffe_config}")

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

    # Extract loader configuration
    loader_config = griffe_config.get("loader", {})

    # Separate loader init kwargs from method calls
    loader_kwargs = {}
    method_calls = {}

    for key, value in loader_config.items():
        if isinstance(value, dict):
            # This is a method call configuration
            method_calls[key] = value
        else:
            # This is a loader init kwarg
            loader_kwargs[key] = value

    logger.info(f"Loader kwargs: {loader_kwargs}")
    logger.info(f"Method calls: {list(method_calls.keys())}")

    # Create GriffeLoader instance
    try:
        loader = griffe.GriffeLoader(
            search_paths=all_search_paths,
            **loader_kwargs,
        )
    except TypeError as e:
        logger.error(f"Invalid loader configuration: {e}")
        raise ModuleLoadError(f"Invalid Griffe loader options: {e}") from e

    # Execute the main load call
    load_kwargs = method_calls.get("load", {})
    logger.info(f"Loading target '{target}' with kwargs: {load_kwargs}")

    try:
        griffe_obj = loader.load(target, **load_kwargs)
    except griffe.LoadingError as e:
        logger.error(f"Griffe LoadingError for '{target}': {e}")
        raise ModuleLoadError(f"Target '{target}' not found: {e}") from e
    except (ImportError, ModuleNotFoundError) as e:
        logger.error(f"Module import error for '{target}': {e}")
        raise ModuleLoadError(f"Target '{target}' not found: {e}") from e
    except TypeError as e:
        logger.error(f"Invalid load options for '{target}': {e}")
        raise ModuleLoadError(f"Invalid load options for '{target}': {e}") from e

    if griffe_obj is None:
        logger.error(f"Griffe returned None for target '{target}'")
        raise ModuleLoadError(f"Target '{target}' not found")

    # Execute any other method calls on the loader
    for method_name, method_kwargs in method_calls.items():
        if method_name == "load":
            continue  # Already handled above

        if not hasattr(loader, method_name):
            logger.warning(f"Loader has no method '{method_name}', skipping")
            continue

        try:
            logger.info(f"Calling loader.{method_name}({method_kwargs})")
            result = getattr(loader, method_name)(**method_kwargs)
            logger.info(f"Method {method_name} returned: {result}")
        except Exception as e:
            logger.error(f"Method {method_name} failed: {e}")
            raise ModuleLoadError(f"Griffe method '{method_name}' failed: {e}") from e

    logger.info(f"Successfully loaded Griffe object: {type(griffe_obj).__name__}")
    logger.info(f"Object name: {getattr(griffe_obj, 'name', 'unknown')}")
    logger.info(f"Object kind: {getattr(griffe_obj, 'kind', 'unknown')}")

    return griffe_obj
