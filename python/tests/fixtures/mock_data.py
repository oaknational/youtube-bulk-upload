"""Mock data factories for tests"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Note: We'll import from types.models once it's created
# For now, let's create mock data factory functions that return dicts


def create_test_video_data(**kwargs: Any) -> Dict[str, Any]:
    """Create VideoData with defaults"""
    defaults = {
        "drive_link": "https://drive.google.com/file/d/test123/view",
        "title": "Test Video",
        "description": "Test Description",
        "tags": ["test", "video"],
        "unique_id": "test-123",
    }
    return {**defaults, **kwargs}


def create_test_config(**kwargs: Any) -> Dict[str, Any]:
    """Create Config with defaults"""
    defaults = {
        "spreadsheet_id": "test-sheet-id",
        "client_id": "test-client",
        "client_secret": "test-secret",
        "redirect_uri": "http://localhost:3000",
        "sheet_range": "Sheet1!A:E",
        "resume": False,
        "temp_dir": Path("./temp_videos"),
        "progress_file": Path("./upload_progress.json"),
        "log_file": Path("./upload_log.txt"),
    }
    return {**defaults, **kwargs}


def create_test_progress(**kwargs: Any) -> Dict[str, Any]:
    """Create Progress with defaults"""
    defaults = {
        "processed_ids": set(),
        "last_processed_row": 0,
        "failed_uploads": [],
    }
    return {**defaults, **kwargs}


def create_test_failed_upload(**kwargs: Any) -> Dict[str, Any]:
    """Create FailedUpload with defaults"""
    defaults = {
        "unique_id": "test-123",
        "error": "Test error",
        "timestamp": datetime.now(),
    }
    return {**defaults, **kwargs}


def create_test_auth_tokens(**kwargs: Any) -> Dict[str, Any]:
    """Create AuthTokens with defaults"""
    defaults = {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_type": "Bearer",
        "expiry": None,
    }
    return {**defaults, **kwargs}


def create_test_spreadsheet_data(rows: int = 3) -> List[List[str]]:
    """Create mock spreadsheet data"""
    data = [["Drive Link", "Title", "Description", "Tags", "Unique ID"]]
    for i in range(rows):
        data.append(
            [
                f"https://drive.google.com/file/d/test{i}/view",
                f"Test Video {i}",
                f"Description for video {i}",
                "tag1,tag2",
                f"video-{i:03d}",
            ]
        )
    return data
