"""Tests for logging utilities."""

import re
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from utils.logging import create_log_message


class TestCreateLogMessage:
    """Test create_log_message function."""

    def test_message_format(self) -> None:
        """Test that message has correct format."""
        message = "Test log message"
        result = create_log_message(message)

        # Check format: [ISO_TIMESTAMP] message\n
        assert result.startswith("[")
        assert f"] {message}\n" in result
        assert result.endswith("\n")

    def test_iso_timestamp_format(self) -> None:
        """Test that timestamp is valid ISO format."""
        result = create_log_message("test")

        # Extract timestamp between brackets
        match = re.match(r"\[([^\]]+)\]", result)
        assert match is not None
        timestamp_str = match.group(1)

        # Verify it's a valid ISO timestamp
        timestamp = datetime.fromisoformat(timestamp_str)
        assert timestamp.tzinfo is not None  # Should have timezone info

    @patch("src.utils.logging.datetime")
    def test_uses_utc_timezone(self, mock_datetime) -> None:
        """Test that UTC timezone is used."""
        # Mock the datetime to return a specific time
        mock_now = datetime(2023, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.timezone.utc = timezone.utc

        result = create_log_message("test")

        # Verify the mock was called with UTC timezone
        mock_datetime.now.assert_called_once_with(timezone.utc)

        # Check the timestamp in the result
        expected = "[2023-01-15T10:30:45.123456+00:00] test\n"
        assert result == expected

    def test_empty_message(self) -> None:
        """Test handling of empty message."""
        result = create_log_message("")

        # Should still have timestamp and newline
        assert re.match(r"\[[^\]]+\] \n", result)

    def test_message_with_newlines(self) -> None:
        """Test message containing newlines."""
        message = "Line 1\nLine 2\nLine 3"
        result = create_log_message(message)

        # Message should be preserved as-is
        assert f"] {message}\n" in result

    def test_message_with_special_characters(self) -> None:
        """Test message with special characters."""
        message = "Special chars: !@#$%^&*(){}[]|\\:;\"'<>,.?/"
        result = create_log_message(message)

        assert f"] {message}\n" in result

    def test_unicode_message(self) -> None:
        """Test message with unicode characters."""
        message = "Unicode: 你好世界 🌍 émojis"
        result = create_log_message(message)

        assert f"] {message}\n" in result

    def test_very_long_message(self) -> None:
        """Test handling of very long messages."""
        message = "x" * 10000  # 10k character message
        result = create_log_message(message)

        assert f"] {message}\n" in result
        assert len(result) > 10000  # Should include timestamp + message + newline

    def test_timestamp_precision(self) -> None:
        """Test that timestamp includes microseconds."""
        result = create_log_message("test")

        # Extract timestamp
        match = re.match(r"\[([^\]]+)\]", result)
        assert match is not None
        timestamp_str = match.group(1)

        # Check for microseconds (6 digits after the decimal)
        assert re.search(r"\.\d{6}", timestamp_str) is not None
