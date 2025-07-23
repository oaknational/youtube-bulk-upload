"""Tests for error printer utility."""

from io import StringIO
from unittest.mock import patch

import pytest

from utils.error_printer import print_missing_config_error


class TestPrintMissingConfigError:
    """Test print_missing_config_error function."""

    @patch("builtins.print")
    def test_no_missing_fields(self, mock_print) -> None:
        """Test that nothing is printed when no fields are missing."""
        print_missing_config_error([])

        # Should not call print at all
        mock_print.assert_not_called()

    @patch("builtins.print")
    def test_single_missing_field(self, mock_print) -> None:
        """Test printing error for single missing field."""
        print_missing_config_error(["clientId"])

        # Check the calls
        calls = mock_print.call_args_list
        assert len(calls) == 6  # Error + blank + header + 4 env vars + help

        # Check first error message
        assert calls[0][0][0] == "Error: Missing required configuration field: clientId"

        # Check environment variables section
        assert calls[2][0][0] == "Required environment variables:"
        assert calls[3][0][0] == "- GOOGLE_CLIENT_ID"
        assert calls[4][0][0] == "- GOOGLE_CLIENT_SECRET"
        assert calls[5][0][0] == "- GOOGLE_REDIRECT_URI"

    @patch("builtins.print")
    def test_multiple_missing_fields_shows_first(self, mock_print) -> None:
        """Test that only the first missing field is shown in error message."""
        print_missing_config_error(["clientId", "clientSecret", "spreadsheetId"])

        # Should show first field only
        first_call = mock_print.call_args_list[0][0][0]
        assert first_call == "Error: Missing required configuration field: clientId"

    def test_complete_output_format(self, capsys) -> None:
        """Test the complete output format using capsys."""
        print_missing_config_error(["spreadsheetId"])

        captured = capsys.readouterr()
        expected = """Error: Missing required configuration field: spreadsheetId

Required environment variables:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI
- SPREADSHEET_ID

Please set these environment variables and try again.
"""

        assert captured.out == expected

    @patch("builtins.print")
    def test_empty_list_behavior(self, mock_print) -> None:
        """Test behavior with empty list (edge case)."""
        print_missing_config_error([])
        mock_print.assert_not_called()

    def test_all_env_vars_listed(self, capsys) -> None:
        """Test that all required environment variables are listed."""
        print_missing_config_error(["clientSecret"])

        captured = capsys.readouterr()

        # Check all required env vars are mentioned
        assert "GOOGLE_CLIENT_ID" in captured.out
        assert "GOOGLE_CLIENT_SECRET" in captured.out
        assert "GOOGLE_REDIRECT_URI" in captured.out
        assert "SPREADSHEET_ID" in captured.out

    def test_help_message_included(self, capsys) -> None:
        """Test that help message is included."""
        print_missing_config_error(["redirectUri"])

        captured = capsys.readouterr()

        assert "Please set these environment variables and try again." in captured.out

    @patch("sys.stdout", new_callable=StringIO)
    def test_output_to_stdout_not_stderr(self, mock_stdout) -> None:
        """Test that output goes to stdout, not stderr."""
        print_missing_config_error(["clientId"])

        output = mock_stdout.getvalue()
        assert "Error: Missing required configuration field: clientId" in output

    def test_field_name_preserved(self, capsys) -> None:
        """Test that field names are preserved as provided."""
        # Test with different casing
        test_cases = [
            "clientId",
            "ClientId",
            "client_id",
            "CLIENTID",
        ]

        for field_name in test_cases:
            print_missing_config_error([field_name])
            captured = capsys.readouterr()
            assert f"Error: Missing required configuration field: {field_name}" in captured.out
