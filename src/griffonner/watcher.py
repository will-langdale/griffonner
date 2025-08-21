"""File system watcher for Griffonner."""

import time
from pathlib import Path
from typing import List, Optional

import typer
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .core import generate_file
from .frontmatter import find_frontmatter_files


class GriffonnerEventHandler(FileSystemEventHandler):
    """Handles file system events for Griffonner."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        template_dirs: Optional[List[Path]] = None,
    ) -> None:
        """Initialize the event handler.

        Args:
            source_dir: Directory to watch for changes
            output_dir: Output directory for generated files
            template_dirs: Additional template directories
        """
        super().__init__()
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.template_dirs = template_dirs or []

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Only process files with frontmatter (markdown files)
        if file_path.suffix.lower() in [".md", ".markdown"]:
            self._regenerate_file(file_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(str(event.src_path))

        # Only process files with frontmatter (markdown files)
        if file_path.suffix.lower() in [".md", ".markdown"]:
            self._regenerate_file(file_path)

    def _regenerate_file(self, file_path: Path) -> None:
        """Regenerate documentation for a single file.

        Args:
            file_path: Path to the file that changed
        """
        try:
            # Check if file is within our source directory and has frontmatter
            relative_path = file_path.relative_to(self.source_dir)

            # Verify the file has frontmatter by checking if it's in our list
            frontmatter_files = find_frontmatter_files(self.source_dir)
            if file_path not in frontmatter_files:
                return  # Not a frontmatter file, ignore

            # Generate the file
            generated_files = generate_file(
                file_path, self.output_dir, self.template_dirs
            )

            file_count = len(generated_files)
            typer.echo(f"🔄 Regenerated {file_count} files from {relative_path}:")
            for generated_file in generated_files:
                rel_generated = generated_file.relative_to(self.output_dir)
                typer.echo(f"  📄 {rel_generated}")

        except ValueError:
            # File is not within source directory, ignore
            return
        except Exception as e:
            typer.echo(f"❌ Failed to regenerate {file_path}: {e}", err=True)


class DocumentationWatcher:
    """Watches for changes in documentation source files."""

    def __init__(
        self,
        source_dir: Path,
        output_dir: Path,
        template_dirs: Optional[List[Path]] = None,
    ) -> None:
        """Initialize the documentation watcher.

        Args:
            source_dir: Directory to watch for changes
            output_dir: Output directory for generated files
            template_dirs: Additional template directories
        """
        self.source_dir = source_dir.resolve()
        self.output_dir = output_dir.resolve()
        self.template_dirs = template_dirs or []

        self.observer = Observer()
        self.event_handler = GriffonnerEventHandler(
            self.source_dir, self.output_dir, self.template_dirs
        )

    def start(self) -> None:
        """Start watching for file changes."""
        if not self.source_dir.exists():
            raise FileNotFoundError(f"Source directory not found: {self.source_dir}")

        if not self.source_dir.is_dir():
            msg = f"Source path is not a directory: {self.source_dir}"
            raise NotADirectoryError(msg)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Start watching
        self.observer.schedule(self.event_handler, str(self.source_dir), recursive=True)
        self.observer.start()

        typer.echo(f"👀 Watching {self.source_dir} for changes...")
        typer.echo(f"📂 Output directory: {self.output_dir}")
        typer.echo("Press Ctrl+C to stop")

    def stop(self) -> None:
        """Stop watching for file changes."""
        self.observer.stop()
        self.observer.join()

    def watch(self) -> None:
        """Start watching and block until interrupted."""
        self.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            typer.echo("\n🛑 Stopping watcher...")
            self.stop()
            typer.echo("✅ Watcher stopped")
