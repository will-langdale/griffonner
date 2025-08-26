"""File system watcher for Griffonner."""

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import typer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .core import generate_file
from .frontmatter import find_frontmatter_files

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
    ) -> None:
        """Initialise the event handler.

        Args:
            source_dir: Directory to watch for changes
            output_dir: Output directory for generated files
            template_dirs: Additional template directories
            plugin_manager: Optional plugin manager for processors/filters
        """
        super().__init__()
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.template_dirs = template_dirs or []
        self.plugin_manager = plugin_manager

        logger.info(f"Initialised event handler - source: {source_dir}")
        logger.info(f"Template directories: {self.template_dirs}")
        logger.info(
            f"Plugin manager: {'provided' if plugin_manager else 'not provided'}"
        )

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

        # Process all files that might have frontmatter
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

        # Process all files that might have frontmatter
        logger.info(f"Processing file creation: {file_path}")
        self._regenerate_file(file_path)

    def _regenerate_file(self, file_path: Path) -> None:
        """Regenerate documentation for a single file.

        Args:
            file_path: Path to the file that changed
        """
        logger.info(f"Attempting to regenerate file: {file_path}")

        try:
            # Check if file is within our source directory and has frontmatter
            logger.info("Checking if file is within source directory")
            relative_path = file_path.relative_to(self.source_dir)
            logger.info(f"File relative path: {relative_path}")

            # Verify the file has frontmatter by checking if it's in our list
            logger.info("Checking for frontmatter files in source directory")
            frontmatter_files = find_frontmatter_files(self.source_dir)
            if file_path not in frontmatter_files:
                logger.info("File not in frontmatter files list, ignoring")
                return  # Not a frontmatter file, ignore

            logger.info("File confirmed as frontmatter file, proceeding")
            # Generate the file
            generated_files = generate_file(
                file_path, self.output_dir, self.template_dirs, self.plugin_manager
            )

            file_count = len(generated_files)
            typer.echo(f"🔄 Regenerated {file_count} files from {relative_path}:")
            for generated_file in generated_files:
                rel_generated = generated_file.relative_to(self.output_dir)
                typer.echo(f"  📄 {rel_generated}")

            logger.info(f"File regeneration successful: {file_count} files generated")

        except ValueError as e:
            # File is not within source directory, ignore
            logger.info(f"File not within source directory, ignoring ({e})")
            return
        except Exception as e:
            logger.exception(f"File regeneration failed for {file_path}")
            typer.echo(f"❌ Failed to regenerate {file_path}: {e}", err=True)


class DocumentationWatcher:
    """Watches for changes in documentation source files."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        template_dirs: Optional[List[Path]] = None,
        plugin_manager: Optional["PluginManager"] = None,
    ) -> None:
        """Initialise the documentation watcher.

        Args:
            source_dir: Directory to watch for changes
            output_dir: Output directory for generated files
            template_dirs: Additional template directories
            plugin_manager: Optional plugin manager for processors/filters
        """
        self.source_dir = source_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.template_dirs = template_dirs or []
        self.plugin_manager = plugin_manager

        logger.info("Initialising DocumentationWatcher")
        logger.info(f"Source directory: {self.source_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Template directories: {self.template_dirs}")
        logger.info(
            f"Plugin manager: {'provided' if plugin_manager else 'not provided'}"
        )

        self.observer = Observer()
        self.event_handler = GriffonnerEventHandler(
            self.source_dir, self.output_dir, self.template_dirs, self.plugin_manager
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
