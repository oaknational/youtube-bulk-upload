"""Build configuration from environment variables."""

import os
from typing import Optional

from models import Config


def build_config_from_env(override_spreadsheet_id: Optional[str] = None) -> Config:
    """
    Construct a Config object from environment variables.

    Args:
        override_spreadsheet_id: Optional spreadsheet ID to override env var

    Returns:
        Config object with values from environment
    """
    return Config(
        client_id=os.environ.get("GOOGLE_CLIENT_ID", ""),
        client_secret=os.environ.get("GOOGLE_CLIENT_SECRET", ""),
        redirect_uri=os.environ.get("GOOGLE_REDIRECT_URI", ""),
        spreadsheet_id=override_spreadsheet_id or os.environ.get("SPREADSHEET_ID", ""),
        sheet_range=os.environ.get("SHEET_RANGE", "A:E"),
        progress_file=os.environ.get("PROGRESS_FILE", "progress.json"),
        log_file=os.environ.get("LOG_FILE", "upload.log"),
        token_file=os.environ.get("TOKEN_FILE", "token.json"),
        temp_dir=os.environ.get("TEMP_DIR", "./temp"),
    )
