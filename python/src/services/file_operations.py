"""File operations service implementation."""

import os
from io import BufferedReader, BufferedWriter
from os import PathLike, stat_result
from pathlib import Path
from typing import Optional, Union

from interfaces import IFileOperations


class FileOperations(IFileOperations):
    """Implementation of file system operations."""

    def read_file(self, path: Union[str, PathLike[str]]) -> str:
        """
        Read file contents synchronously.

        Args:
            path: Path to file

        Returns:
            File contents

        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If no read permission
        """
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def write_file(self, path: Union[str, PathLike[str]], content: str) -> None:
        """
        Write content to file.

        Args:
            path: Path to file
            content: Content to write
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def append_file(self, path: Union[str, PathLike[str]], content: str) -> None:
        """
        Append to existing file.

        Args:
            path: Path to file
            content: Content to append
        """
        with open(path, "a", encoding="utf-8") as f:
            f.write(content)

    def exists(self, path: Union[str, PathLike[str]]) -> bool:
        """
        Check if file/directory exists.

        Args:
            path: Path to check

        Returns:
            True if exists
        """
        return Path(path).exists()

    def unlink(self, path: Union[str, PathLike[str]]) -> None:
        """
        Delete file.

        Args:
            path: Path to file

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        Path(path).unlink()

    def mkdir(self, path: Union[str, PathLike[str]], exist_ok: bool = False) -> None:
        """
        Create directory.

        Args:
            path: Path to directory
            exist_ok: If True, don't raise if exists
        """
        Path(path).mkdir(parents=True, exist_ok=exist_ok)

    def create_read_stream(self, path: Union[str, PathLike[str]]) -> BufferedReader:
        """
        Create readable stream.

        Args:
            path: Path to file

        Returns:
            Buffered reader
        """
        return open(path, "rb")

    def create_write_stream(self, path: Union[str, PathLike[str]]) -> BufferedWriter:
        """
        Create writable stream.

        Args:
            path: Path to file

        Returns:
            Buffered writer
        """
        return open(path, "wb")

    def stat(self, path: Union[str, PathLike[str]]) -> stat_result:
        """
        Get file statistics.

        Args:
            path: Path to file

        Returns:
            File statistics
        """
        return os.stat(path)
