"""Logging utility functions."""

from datetime import datetime, timezone


def create_log_message(message: str) -> str:
    """
    Create a formatted log message with ISO timestamp.

    Args:
        message: The message to log

    Returns:
        Formatted message with timestamp and newline
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    return f"[{timestamp}] {message}\n"
