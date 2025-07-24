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


def print_user_friendly_error(error: Exception) -> None:
    """
    Print user-friendly error messages for common exceptions.

    Args:
        error: The exception that occurred
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Handle specific error types with custom messages
    if error_type == "FileNotFoundError":
        print(f"Error: File not found - {error_msg}")
        print("\nPlease ensure the file exists and the path is correct.")
    elif error_type == "PermissionError":
        print(f"Error: Permission denied - {error_msg}")
        print("\nPlease check file permissions or try running with appropriate privileges.")
    elif error_type == "ConnectionError":
        print(f"Error: Connection failed - {error_msg}")
        print("\nPlease check your internet connection and try again.")
    elif error_type == "ValueError" and "Configuration errors" in error_msg:
        print(f"Error: {error_msg}")
        print("\nPlease check your configuration and try again.")
    elif error_type == "ValueError" and "Credentials file not found" in error_msg:
        print(f"Error: {error_msg}")
    elif "google" in error_type.lower() or "api" in error_type.lower():
        print(f"Error: Google API error - {error_msg}")
        print("\nPlease check your API credentials and permissions.")
    else:
        # Generic error handling
        print(f"Error: {error_type} - {error_msg}")
        print("\nAn unexpected error occurred. Please check the logs for more details.")
