"""Tests for FileOperations service."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from services.file_operations import FileOperations


class TestFileOperations:
    """Test FileOperations service."""

    @pytest.fixture
    def file_ops(self):
        """Create FileOperations instance."""
        return FileOperations()

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as f:
            f.write("test content")
            temp_path = f.name
        yield temp_path
        # Cleanup
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory."""
        with tempfile.TemporaryDirectory() as d:
            yield d

    def test_read_file_success(self, file_ops, temp_file):
        """Test successful file read."""
        content = file_ops.read_file(temp_file)
        assert content == "test content"

    def test_read_file_not_found(self, file_ops):
        """Test reading non-existent file."""
        with pytest.raises(FileNotFoundError):
            file_ops.read_file("/nonexistent/file.txt")

    def test_write_file(self, file_ops, temp_dir):
        """Test writing to file."""
        file_path = Path(temp_dir) / "test.txt"
        file_ops.write_file(file_path, "new content")

        assert file_path.exists()
        assert file_path.read_text() == "new content"

    def test_write_file_overwrites(self, file_ops, temp_file):
        """Test that write_file overwrites existing content."""
        file_ops.write_file(temp_file, "overwritten")

        content = file_ops.read_file(temp_file)
        assert content == "overwritten"

    def test_append_file(self, file_ops, temp_file):
        """Test appending to file."""
        file_ops.append_file(temp_file, " appended")

        content = file_ops.read_file(temp_file)
        assert content == "test content appended"

    def test_append_file_creates_if_not_exists(self, file_ops, temp_dir):
        """Test that append creates file if it doesn't exist."""
        file_path = Path(temp_dir) / "new.txt"
        file_ops.append_file(file_path, "created")

        assert file_path.exists()
        assert file_path.read_text() == "created"

    def test_exists_file(self, file_ops, temp_file):
        """Test checking if file exists."""
        assert file_ops.exists(temp_file) is True
        assert file_ops.exists("/nonexistent/file.txt") is False

    def test_exists_directory(self, file_ops, temp_dir):
        """Test checking if directory exists."""
        assert file_ops.exists(temp_dir) is True
        assert file_ops.exists("/nonexistent/dir") is False

    def test_unlink_file(self, file_ops, temp_file):
        """Test deleting file."""
        assert Path(temp_file).exists()
        file_ops.unlink(temp_file)
        assert not Path(temp_file).exists()

    def test_unlink_nonexistent(self, file_ops):
        """Test deleting non-existent file."""
        with pytest.raises(FileNotFoundError):
            file_ops.unlink("/nonexistent/file.txt")

    def test_mkdir(self, file_ops, temp_dir):
        """Test creating directory."""
        new_dir = Path(temp_dir) / "subdir" / "nested"
        file_ops.mkdir(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_mkdir_exist_ok(self, file_ops, temp_dir):
        """Test creating directory that already exists."""
        # Should not raise when exist_ok=True
        file_ops.mkdir(temp_dir, exist_ok=True)

        # Should raise when exist_ok=False (default)
        with pytest.raises(FileExistsError):
            file_ops.mkdir(temp_dir, exist_ok=False)

    def test_create_read_stream(self, file_ops, temp_file):
        """Test creating read stream."""
        with file_ops.create_read_stream(temp_file) as stream:
            content = stream.read()
            assert content == b"test content"

    def test_create_write_stream(self, file_ops, temp_dir):
        """Test creating write stream."""
        file_path = Path(temp_dir) / "stream.txt"

        with file_ops.create_write_stream(file_path) as stream:
            stream.write(b"binary content")

        assert file_path.exists()
        assert file_path.read_bytes() == b"binary content"

    def test_stat(self, file_ops, temp_file):
        """Test getting file statistics."""
        stat = file_ops.stat(temp_file)

        assert stat.st_size == len("test content")
        assert hasattr(stat, "st_mtime")
        assert hasattr(stat, "st_mode")

    def test_implements_protocol(self):
        """Test that FileOperations implements IFileOperations protocol."""
        from interfaces import IFileOperations

        file_ops = FileOperations()
        # This would fail at runtime if protocol not satisfied
        _: IFileOperations = file_ops
