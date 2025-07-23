"""Serialize and deserialize progress data."""

import json
from typing import Any, Dict

from models import UploadProgress


def serialize_progress(progress: UploadProgress) -> str:
    """
    Convert UploadProgress object to JSON string for persistence.

    Args:
        progress: UploadProgress object to serialize

    Returns:
        Pretty-printed JSON string
    """
    return json.dumps(progress.to_dict(), indent=2)


def deserialize_progress(data: str) -> UploadProgress:
    """
    Parse JSON string into UploadProgress object.

    Args:
        data: JSON string to parse

    Returns:
        UploadProgress object (empty if parse fails)
    """
    try:
        parsed_data = json.loads(data)
        return UploadProgress.from_dict(parsed_data)
    except (json.JSONDecodeError, KeyError, TypeError):
        # Return empty progress on any parse failure
        return UploadProgress()
