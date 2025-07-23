"""Google Drive utility functions."""

import re
from typing import Optional


def extract_file_id_from_drive_link(link: str) -> Optional[str]:
    """
    Extract the file ID from various Google Drive URL formats.

    Args:
        link: Google Drive URL

    Returns:
        File ID if found, None otherwise
    """
    # Define regex patterns for different Drive URL formats
    patterns = [
        r"/file/d/([a-zA-Z0-9-_]+)",  # Standard file URL
        r"id=([a-zA-Z0-9-_]+)",  # Query parameter format
        r"/open\?id=([a-zA-Z0-9-_]+)",  # Open link format
    ]

    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)

    return None
