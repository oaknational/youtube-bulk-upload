"""Tests for Logger service."""

from io import StringIO
from unittest.mock import Mock, patch

import pytest

from interfaces import IFileOperations
from services.logger import Logger


class TestLogger:
    """Test Logger service."""

    @pytest.fixture
    def mock_file_ops(self):
        """Create mock file operations."""
        return Mock(spec=IFileOperations)

    @pytest.fixture
    def logger(self, mock_file_ops):
        """Create Logger instance."""
        return Logger(mock_file_ops, "test.log")

    @patch("builtins.print")
    def test_log_message(self, mock_print, logger, mock_file_ops):
        """Test logging info message."""
        logger.log("Test message")

        # Verify console output (without trailing newline)
        mock_print.assert_called_once()
        printed_msg = mock_print.call_args[0][0]
        assert "Test message" in printed_msg
        assert printed_msg.startswith("[")  # Timestamp

        # Verify file append
        mock_file_ops.append_file.assert_called_once()
        file_path, content = mock_file_ops.append_file.call_args[0]
        assert file_path == "test.log"
        assert "Test message" in content
        assert content.endswith("\n")

    @patch("builtins.print")
    def test_error_message(self, mock_print, logger, mock_file_ops):
        """Test logging error message."""
        logger.error("Something went wrong")

        # Check that ERROR prefix is added
        printed_msg = mock_print.call_args[0][0]
        assert "ERROR: Something went wrong" in printed_msg

        # Check file content
        file_content = mock_file_ops.append_file.call_args[0][1]
        assert "ERROR: Something went wrong" in file_content

    @patch("builtins.print")
    def test_warn_message(self, mock_print, logger, mock_file_ops):
        """Test logging warning message."""
        logger.warn("This is a warning")

        # Check that WARN prefix is added
        printed_msg = mock_print.call_args[0][0]
        assert "WARN: This is a warning" in printed_msg

        # Check file content
        file_content = mock_file_ops.append_file.call_args[0][1]
        assert "WARN: This is a warning" in file_content

    @patch("builtins.print")
    def test_multiple_logs(self, mock_print, logger, mock_file_ops):
        """Test multiple log calls."""
        logger.log("First")
        logger.error("Second")
        logger.warn("Third")

        assert mock_print.call_count == 3
        assert mock_file_ops.append_file.call_count == 3

    @patch("builtins.print")
    def test_empty_message(self, mock_print, logger, mock_file_ops):
        """Test logging empty message."""
        logger.log("")

        # Should still log with timestamp
        mock_print.assert_called_once()
        printed_msg = mock_print.call_args[0][0]
        assert printed_msg.startswith("[")
        assert printed_msg.endswith("]")

    @patch("builtins.print")
    def test_multiline_message(self, mock_print, logger, mock_file_ops):
        """Test logging multiline message."""
        message = "Line 1\nLine 2\nLine 3"
        logger.log(message)

        # Message should be preserved
        file_content = mock_file_ops.append_file.call_args[0][1]
        assert message in file_content

    def test_file_operations_error_propagates(self, logger, mock_file_ops):
        """Test that file operations errors propagate."""
        mock_file_ops.append_file.side_effect = PermissionError("No write access")

        with pytest.raises(PermissionError):
            logger.log("Test")

    def test_different_log_file(self, mock_file_ops):
        """Test using different log file path."""
        logger = Logger(mock_file_ops, "/var/log/app.log")
        logger.log("Test")

        file_path = mock_file_ops.append_file.call_args[0][0]
        assert file_path == "/var/log/app.log"

    def test_implements_protocol(self, mock_file_ops):
        """Test that Logger implements ILogger protocol."""
        from interfaces import ILogger

        logger = Logger(mock_file_ops, "test.log")
        # This would fail at runtime if protocol not satisfied
        _: ILogger = logger
