"""Core type definitions for YouTube Bulk Upload."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Set


@dataclass
class VideoData:
    """Represents metadata for a single video to be uploaded."""

    drive_link: str
    title: str
    description: str
    tags: List[str]
    unique_id: str

    def __post_init__(self) -> None:
        """Validate video data after initialization."""
        if not self.drive_link:
            raise ValueError("drive_link cannot be empty")
        if not self.title:
            raise ValueError("title cannot be empty")
        if not self.unique_id:
            raise ValueError("unique_id cannot be empty")


@dataclass
class FailedUpload:
    """Records details about failed upload attempts."""

    unique_id: str
    error: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self) -> None:
        """Validate failed upload data."""
        if not self.unique_id:
            raise ValueError("unique_id cannot be empty")
        if not self.error:
            raise ValueError("error cannot be empty")


@dataclass
class UploadProgress:
    """Tracks the overall progress of bulk upload operations for resume capability."""

    processed_ids: Set[str] = field(default_factory=set)
    last_processed_row: int = 0
    failed_uploads: List[FailedUpload] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "processed_ids": list(self.processed_ids),
            "last_processed_row": self.last_processed_row,
            "failed_uploads": [
                {
                    "unique_id": fu.unique_id,
                    "error": fu.error,
                    "timestamp": fu.timestamp,
                }
                for fu in self.failed_uploads
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UploadProgress":
        """Create UploadProgress from dictionary."""
        return cls(
            processed_ids=set(data.get("processed_ids", [])),
            last_processed_row=data.get("last_processed_row", 0),
            failed_uploads=[
                FailedUpload(**fu) for fu in data.get("failed_uploads", [])
            ],
        )


@dataclass
class Config:
    """Application configuration settings."""

    client_id: str
    client_secret: str
    redirect_uri: str
    spreadsheet_id: str
    sheet_range: str = "A:E"
    progress_file: str = "progress.json"
    log_file: str = "upload.log"
    token_file: str = "token.json"
    temp_dir: str = "./temp"

    def __post_init__(self) -> None:
        """Validate configuration."""
        required_fields = [
            ("client_id", self.client_id),
            ("client_secret", self.client_secret),
            ("redirect_uri", self.redirect_uri),
            ("spreadsheet_id", self.spreadsheet_id),
        ]
        for field_name, value in required_fields:
            if not value:
                raise ValueError(f"{field_name} cannot be empty")


@dataclass
class AuthTokens:
    """OAuth2 token information from Google authentication."""

    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None
    expiry_date: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            k: v
            for k, v in {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "scope": self.scope,
                "token_type": self.token_type,
                "expiry_date": self.expiry_date,
            }.items()
            if v is not None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuthTokens":
        """Create AuthTokens from dictionary."""
        return cls(
            access_token=data.get("access_token"),
            refresh_token=data.get("refresh_token"),
            scope=data.get("scope"),
            token_type=data.get("token_type"),
            expiry_date=data.get("expiry_date"),
        )


__all__ = [
    "VideoData",
    "FailedUpload",
    "UploadProgress",
    "Config",
    "AuthTokens",
]