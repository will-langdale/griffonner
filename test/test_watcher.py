"""Tests for file watcher functionality."""

import pytest
import time
from pathlib import Path
from tempfile import TemporaryDirectory

from griffonner.watcher import DocumentationWatcher, GriffonnerEventHandler


class TestDocumentationWatcher:
    """Tests for DocumentationWatcher."""

    def test_init(self):
        """Test watcher initialization."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = temp_path / "pages"
            source_dir.mkdir()
            output_dir = temp_path / "output"
            
            watcher = DocumentationWatcher(source_dir, output_dir)
            
            assert watcher.source_dir == source_dir.resolve()
            assert watcher.output_dir == output_dir.resolve()
            assert watcher.template_dirs == []

    def test_start_nonexistent_source(self):
        """Test starting watcher with nonexistent source directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            nonexistent_dir = temp_path / "nonexistent"
            output_dir = temp_path / "output"
            
            watcher = DocumentationWatcher(nonexistent_dir, output_dir)
            
            with pytest.raises(FileNotFoundError):
                watcher.start()

    def test_start_source_not_directory(self):
        """Test starting watcher when source is not a directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a file instead of directory
            source_file = temp_path / "source.txt"
            source_file.write_text("content")
            output_dir = temp_path / "output"
            
            watcher = DocumentationWatcher(source_file, output_dir)
            
            with pytest.raises(NotADirectoryError):
                watcher.start()

    def test_creates_output_directory(self):
        """Test that watcher creates output directory if it doesn't exist."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = temp_path / "pages"
            source_dir.mkdir()
            output_dir = temp_path / "output"  # Don't create this
            
            watcher = DocumentationWatcher(source_dir, output_dir)
            watcher.start()
            
            # Should have created output directory
            assert output_dir.exists()
            assert output_dir.is_dir()
            
            watcher.stop()


class TestGriffonnerEventHandler:
    """Tests for GriffonnerEventHandler."""

    def test_init(self):
        """Test event handler initialization."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = temp_path / "pages"
            output_dir = temp_path / "output"
            
            handler = GriffonnerEventHandler(source_dir, output_dir)
            
            assert handler.source_dir == source_dir
            assert handler.output_dir == output_dir
            assert handler.template_dirs == []

    def test_ignores_non_markdown_files(self):
        """Test that handler ignores non-markdown files."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = temp_path / "pages"
            source_dir.mkdir()
            output_dir = temp_path / "output"
            
            handler = GriffonnerEventHandler(source_dir, output_dir)
            
            # Create mock event for non-markdown file
            class MockEvent:
                def __init__(self, path):
                    self.src_path = str(path)
                    self.is_directory = False
            
            # Create a Python file
            python_file = source_dir / "script.py"
            python_file.write_text("print('hello')")
            
            # Should not process Python files (no error should occur)
            event = MockEvent(python_file)
            handler.on_modified(event)  # Should complete without error

    def test_ignores_directories(self):
        """Test that handler ignores directory events."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = temp_path / "pages"
            source_dir.mkdir()
            output_dir = temp_path / "output"
            
            handler = GriffonnerEventHandler(source_dir, output_dir)
            
            # Create mock event for directory
            class MockEvent:
                def __init__(self, path):
                    self.src_path = str(path)
                    self.is_directory = True
            
            # Create a subdirectory
            subdir = source_dir / "subdir"
            subdir.mkdir()
            
            # Should not process directories (no error should occur)
            event = MockEvent(subdir)
            handler.on_modified(event)  # Should complete without error


class TestWatcherIntegration:
    """Integration tests for watcher functionality."""

    def test_watcher_basic_functionality(self):
        """Test basic watcher setup and teardown."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Set up directories
            source_dir = temp_path / "pages"
            source_dir.mkdir()
            output_dir = temp_path / "output"
            
            # Create watcher
            watcher = DocumentationWatcher(source_dir, output_dir)
            
            # Should be able to start and stop without error
            watcher.start()
            time.sleep(0.1)  # Give it a moment
            watcher.stop()
            
            # Output directory should exist
            assert output_dir.exists()

    def test_event_handler_error_handling(self):
        """Test that event handler handles errors gracefully."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            source_dir = temp_path / "pages"
            source_dir.mkdir()
            output_dir = temp_path / "output"
            
            handler = GriffonnerEventHandler(source_dir, output_dir)
            
            # Create mock event for file outside source directory
            class MockEvent:
                def __init__(self, path):
                    self.src_path = str(path)
                    self.is_directory = False
            
            # Create file outside source directory
            outside_file = temp_path / "outside.md"
            outside_file.write_text("---\ntemplate: test\n---\ncontent")
            
            # Should handle this gracefully (file outside source dir)
            event = MockEvent(outside_file)
            handler.on_modified(event)  # Should complete without error