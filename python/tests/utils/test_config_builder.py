"""Tests for config builder utility."""

import os
from unittest.mock import patch

import pytest

from utils.config_builder import build_config_from_env


class TestBuildConfigFromEnv:
    """Test build_config_from_env function."""

    @patch.dict(
        os.environ,
        {
            "GOOGLE_CLIENT_ID": "test_client_id",
            "GOOGLE_CLIENT_SECRET": "test_client_secret",
            "GOOGLE_REDIRECT_URI": "http://localhost:8080/callback",
            "SPREADSHEET_ID": "test_spreadsheet_123",
            "SHEET_RANGE": "Sheet1!A:F",
            "PROGRESS_FILE": "/tmp/progress.json",
            "LOG_FILE": "/var/log/upload.log",
            "TOKEN_FILE": "/home/user/.tokens.json",
            "TEMP_DIR": "/tmp/videos",
        },
    )
    def test_all_env_vars_set(self) -> None:
        """Test building config when all environment variables are set."""
        config = build_config_from_env()

        assert config.client_id == "test_client_id"
        assert config.client_secret == "test_client_secret"
        assert config.redirect_uri == "http://localhost:8080/callback"
        assert config.spreadsheet_id == "test_spreadsheet_123"
        assert config.sheet_range == "Sheet1!A:F"
        assert config.progress_file == "/tmp/progress.json"
        assert config.log_file == "/var/log/upload.log"
        assert config.token_file == "/home/user/.tokens.json"
        assert config.temp_dir == "/tmp/videos"

    @patch.dict(
        os.environ,
        {
            "GOOGLE_CLIENT_ID": "client_id",
            "GOOGLE_CLIENT_SECRET": "client_secret",
            "GOOGLE_REDIRECT_URI": "http://localhost",
            "SPREADSHEET_ID": "sheet_id",
        },
        clear=True,
    )
    def test_only_required_env_vars(self) -> None:
        """Test building config with only required env vars (defaults for optional)."""
        config = build_config_from_env()

        assert config.client_id == "client_id"
        assert config.client_secret == "client_secret"
        assert config.redirect_uri == "http://localhost"
        assert config.spreadsheet_id == "sheet_id"
        # Check defaults
        assert config.sheet_range == "A:E"
        assert config.progress_file == "progress.json"
        assert config.log_file == "upload.log"
        assert config.token_file == "token.json"
        assert config.temp_dir == "./temp"

    @patch.dict(os.environ, {}, clear=True)
    def test_no_env_vars_set(self) -> None:
        """Test building config when no environment variables are set."""
        # Should raise ValueError because required fields are empty
        with pytest.raises(ValueError, match="client_id cannot be empty"):
            build_config_from_env()

    @patch.dict(os.environ, {"SPREADSHEET_ID": "env_sheet_id"})
    def test_override_spreadsheet_id(self) -> None:
        """Test overriding spreadsheet ID via parameter."""
        config = build_config_from_env("override_sheet_id")

        assert config.spreadsheet_id == "override_sheet_id"
        # Other fields should be empty or default
        assert config.client_id == ""

    @patch.dict(os.environ, {"SPREADSHEET_ID": "env_sheet_id"})
    def test_no_override_uses_env(self) -> None:
        """Test that no override uses environment variable."""
        config = build_config_from_env()

        assert config.spreadsheet_id == "env_sheet_id"

    @patch.dict(os.environ, {})
    def test_override_with_no_env_var(self) -> None:
        """Test override when env var is not set."""
        config = build_config_from_env("override_sheet_id")

        assert config.spreadsheet_id == "override_sheet_id"

    @patch.dict(os.environ, {"SPREADSHEET_ID": ""})
    def test_override_with_empty_env_var(self) -> None:
        """Test override when env var is empty string."""
        config = build_config_from_env("override_sheet_id")

        assert config.spreadsheet_id == "override_sheet_id"

    @patch.dict(
        os.environ,
        {
            "GOOGLE_CLIENT_ID": "   padded_id   ",
            "GOOGLE_CLIENT_SECRET": "\tclient_secret\n",
            "GOOGLE_REDIRECT_URI": " http://localhost ",
        },
    )
    def test_env_values_not_trimmed(self) -> None:
        """Test that environment values are not automatically trimmed."""
        config = build_config_from_env()

        # Values should be used as-is from environment
        assert config.client_id == "   padded_id   "
        assert config.client_secret == "\tclient_secret\n"
        assert config.redirect_uri == " http://localhost "

    @patch.dict(
        os.environ,
        {
            "SHEET_RANGE": "",
            "PROGRESS_FILE": "",
            "LOG_FILE": "",
            "TOKEN_FILE": "",
            "TEMP_DIR": "",
        },
    )
    def test_empty_optional_env_vars(self) -> None:
        """Test that empty optional env vars override defaults."""
        config = build_config_from_env()

        # Empty env vars should override defaults
        assert config.sheet_range == ""
        assert config.progress_file == ""
        assert config.log_file == ""
        assert config.token_file == ""
        assert config.temp_dir == ""

    def test_validation_error_propagation(self) -> None:
        """Test that Config validation errors are propagated."""
        # This will create a Config with empty required fields
        # which should raise ValueError from Config.__post_init__
        with pytest.raises(ValueError, match="client_id cannot be empty"):
            build_config_from_env()
