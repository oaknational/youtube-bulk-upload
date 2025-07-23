"""Validate configuration objects."""

from typing import List

from models import Config


def validate_required_config_fields(config: Config) -> List[str]:
    """
    Validate that required configuration fields are present.

    Args:
        config: Config object to validate

    Returns:
        List of missing field names (empty if all present)
    """
    missing_fields = []

    # Check required fields
    required_fields = [
        ("clientId", config.client_id),
        ("clientSecret", config.client_secret),
        ("redirectUri", config.redirect_uri),
        ("spreadsheetId", config.spreadsheet_id),
    ]

    for field_name, value in required_fields:
        if not value:
            missing_fields.append(field_name)

    return missing_fields
