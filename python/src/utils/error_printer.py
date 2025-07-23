"""Print user-friendly error messages."""

from typing import List


def print_missing_config_error(missing_fields: List[str]) -> None:
    """
    Print user-friendly error messages for missing configuration.

    Args:
        missing_fields: List of missing field names
    """
    if not missing_fields:
        return

    # Show the first missing field in the error message
    print(f"Error: Missing required configuration field: {missing_fields[0]}")
    print("\nRequired environment variables:")
    print("- GOOGLE_CLIENT_ID")
    print("- GOOGLE_CLIENT_SECRET")
    print("- GOOGLE_REDIRECT_URI")
    print("- SPREADSHEET_ID")
    print("\nPlease set these environment variables and try again.")
