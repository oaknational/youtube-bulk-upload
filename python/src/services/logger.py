"""Logger service implementation."""

from interfaces import IFileOperations, ILogger
from utils.logging import create_log_message


class Logger(ILogger):
    """Logger implementation with console and file output."""

    def __init__(self, file_operations: IFileOperations, log_file: str) -> None:
        """
        Initialize logger.

        Args:
            file_operations: File operations service
            log_file: Path to log file
        """
        self.file_operations = file_operations
        self.log_file = log_file

    def log(self, message: str) -> None:
        """
        Log informational message.

        Args:
            message: Message to log
        """
        formatted = create_log_message(message)
        # Print to console without newline (create_log_message adds it)
        print(formatted.rstrip())
        # Append to log file
        self.file_operations.append_file(self.log_file, formatted)

    def error(self, message: str) -> None:
        """
        Log error message.

        Args:
            message: Error message to log
        """
        self.log(f"ERROR: {message}")

    def warn(self, message: str) -> None:
        """
        Log warning message.

        Args:
            message: Warning message to log
        """
        self.log(f"WARN: {message}")
