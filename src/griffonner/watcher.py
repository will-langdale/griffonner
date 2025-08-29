"""File system watcher for Griffonner."""

import fnmatch
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import typer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .core import categorise_files, copy_file_passthrough, generate_file

if TYPE_CHECKING:
    from .plugins.manager import PluginManager

logger = logging.getLogger("griffonner.watcher")


class GriffonnerEventHandler(FileSystemEventHandler):
    """Handles file system events for Griffonner."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        template_dirs: Optional[List[Path]] = None,
        plugin_manager: Optional["PluginManager"] = None,
        ignore_patterns: Optional[List[str]] = None,
        default_griffe_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialise the event handler.

        Args:
            source_dir: Directory to watch for changes
            output_dir: Output directory for generated files
            template_dirs: Additional template directories
            plugin_manager: Optional plugin manager for processors/filters
            ignore_patterns: Glob patterns to ignore
            default_griffe_config: Default Griffe config to merge with frontmatter
        """
        super().__init__()
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.template_dirs = template_dirs or []
        self.plugin_manager = plugin_manager
        self.ignore_patterns = ignore_patterns or []
        self.default_griffe_config = default_griffe_config or {}

        logger.info(f"Initialised event handler - source: {source_dir}")
        logger.info(f"Template directories: {self.template_dirs}")
        logger.info(f"Ignore patterns: {self.ignore_patterns}")
        logger.info(f"Default Griffe config: {self.default_griffe_config}")
        logger.info(
            f"Plugin manager: {'provided' if plugin_manager else 'not provided'}"
        )

    def _should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored based on ignore patterns.

        Args:
            file_path: Path to check

        Returns:
            True if file should be ignored
        """
        if not self.ignore_patterns:
            return False

        try:
            relative_path = file_path.relative_to(self.source_dir)
            # Normalise path for consistent matching across platforms
            relative_str = str(relative_path).replace("\\", "/")

            for pattern in self.ignore_patterns:
                if fnmatch.fnmatch(relative_str, pattern):
                    logger.info(
                        f"Ignoring file {file_path} (matches pattern '{pattern}')"
                    )
                    return True
        except ValueError:
            # File is not within source directory
            return True

        return False

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        logger.info(f"File modified event: {str(event.src_path)}")

        if event.is_directory:
            logger.info("Ignoring directory modification event")
            return

        file_path = Path(str(event.src_path))
        logger.info(f"File modified: {file_path}")

        # Check if file should be ignored
        if self._should_ignore(file_path):
            return

        # Process all files (frontmatter and passthrough)
        logger.info(f"Processing file modification: {file_path}")
        self._regenerate_file(file_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: File system event
        """
        logger.info(f"File created event: {str(event.src_path)}")

        if event.is_directory:
            logger.info("Ignoring directory creation event")
            return

        file_path = Path(str(event.src_path))
        logger.info(f"File created: {file_path}")

        # Check if file should be ignored
        if self._should_ignore(file_path):
            return

        # Process all files (frontmatter and passthrough)
        logger.info(f"Processing file creation: {file_path}")
        self._regenerate_file(file_path)

    def _regenerate_file(self, file_path: Path) -> None:
        """Regenerate documentation for a single file.

        Args:
            file_path: Path to the file that changed
        """
        logger.info(f"Attempting to process file: {file_path}")

        try:
            # Check if file is within our source directory
            logger.info("Checking if file is within source directory")
            relative_path = file_path.relative_to(self.source_dir)
            logger.info(f"File relative path: {relative_path}")

            # Check if file is readable (skip if not)
            try:
                file_path.read_text(encoding="utf-8", errors="strict")
            except (UnicodeDecodeError, PermissionError, OSError) as e:
                logger.warning(f"Skipping unreadable file {file_path}: {e}")
                return

            # Categorise the file
            logger.info("Categorising file type")
            frontmatter_files, passthrough_files = categorise_files([file_path])

            if frontmatter_files:
                # File has frontmatter - generate using templates
                logger.info("File confirmed as frontmatter file, generating")
                generated_files = generate_file(
                    file_path,
                    self.source_dir,
                    self.output_dir,
                    self.template_dirs,
                    self.plugin_manager,
                    self.default_griffe_config,
                )

                file_count = len(generated_files)
                typer.echo(f"🔄 Regenerated {file_count} files from {relative_path}:")
                for generated_file in generated_files:
                    rel_generated = generated_file.relative_to(self.output_dir)
                    typer.echo(f"  📄 {rel_generated}")

                logger.info(f"File generation successful: {file_count} files generated")

            elif passthrough_files:
                # File is passthrough - copy directly
                logger.info("File confirmed as passthrough file, copying")
                copied_file = copy_file_passthrough(
                    file_path, self.source_dir, self.output_dir
                )

                rel_copied = copied_file.relative_to(self.output_dir)
                typer.echo(f"🔄 Copied passthrough file {relative_path}:")
                typer.echo(f"  📄 {rel_copied}")

                logger.info(f"File copy successful: {file_path} -> {copied_file}")
            else:
                logger.warning(f"File {file_path} could not be categorised, ignoring")

        except ValueError as e:
            # File is not within source directory, ignore
            logger.info(f"File not within source directory, ignoring ({e})")
            return
        except Exception as e:
            logger.exception(f"File processing failed for {file_path}")
            typer.echo(f"❌ Failed to process {file_path}: {e}", err=True)


class DocumentationWatcher:
    """Watches for changes in documentation source files."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        template_dirs: Optional[List[Path]] = None,
        plugin_manager: Optional["PluginManager"] = None,
        ignore_patterns: Optional[List[str]] = None,
        default_griffe_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialise the documentation watcher.

        Args:
            source_dir: Directory to watch for changes
            output_dir: Output directory for generated files
            template_dirs: Additional template directories
            plugin_manager: Optional plugin manager for processors/filters
            ignore_patterns: Glob patterns to ignore
            default_griffe_config: Default Griffe config to merge with frontmatter
        """
        self.source_dir = source_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.template_dirs = template_dirs or []
        self.plugin_manager = plugin_manager
        self.ignore_patterns = ignore_patterns or []
        self.default_griffe_config = default_griffe_config or {}

        logger.info("Initialising DocumentationWatcher")
        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Template directories: {self.template_dirs}")
        logger.info(f"Ignore patterns: {self.ignore_patterns}")
        logger.info(f"Default Griffe config: {self.default_griffe_config}")
        logger.info(
            f"Plugin manager: {'provided' if plugin_manager else 'not provided'}"
        )

        self.observer = Observer()
        self.event_handler = GriffonnerEventHandler(
            self.source_dir,
            self.output_dir,
            self.template_dirs,
            self.plugin_manager,
            self.ignore_patterns,
            self.default_griffe_config,
        )
        logger.info("DocumentationWatcher initialised")

    def start(self) -> None:
        """Start watching for file changes."""
        logger.info("Starting documentation watcher")

        if not self.source_dir.exists():
            logger.error(f"Source directory not found: {self.source_dir}")
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        if not self.source_dir.is_dir():
            msg = f"Source path is not a directory: {self.source_dir}"
            logger.error(msg)
            raise NotADirectoryError(msg)

        logger.info("Source directory validation passed")

        # Create output directory if it doesn't exist
        logger.info(f"Creating output directory if needed: {self.output_dir}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Start watching
        logger.info(f"Scheduling observer for directory: {self.source_dir}")
        self.observer.schedule(self.event_handler, str(self.source_dir), recursive=True)
        logger.info("Starting file system observer")
        self.observer.start()

        typer.echo(f"👀 Watching {self.source_dir} for changes...")
        typer.echo(f"📂 Output directory: {self.output_dir}")
        typer.echo("Press Ctrl+C to stop")
        logger.info("Documentation watcher started successfully")

    def stop(self) -> None:
        """Stop watching for file changes."""
        logger.info("Stopping documentation watcher")
        self.observer.stop()
        logger.info("Waiting for observer to join")
        self.observer.join()
        logger.info("Documentation watcher stopped")

    def watch(self) -> None:
        """Start watching and block until interrupted."""
        logger.info("Starting watch mode (blocking)")
        self.start()

        try:
            logger.info("Entering watch loop, waiting for keyboard interrupt")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            typer.echo("\n🛑 Stopping watcher...")
            self.stop()
            typer.echo("✅ Watcher stopped")
