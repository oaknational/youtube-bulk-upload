"""Service interfaces (Protocols) for dependency injection."""

from abc import abstractmethod
from io import BufferedReader, BufferedWriter
from os import PathLike, stat_result
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload

from src.types import AuthTokens, UploadProgress, VideoData


class ILogger(Protocol):
    """Logging operations interface."""

    @abstractmethod
    def log(self, message: str) -> None:
        """Log informational message."""
        ...

    @abstractmethod
    def error(self, message: str) -> None:
        """Log error message."""
        ...

    @abstractmethod
    def warn(self, message: str) -> None:
        """Log warning message."""
        ...


class IFileOperations(Protocol):
    """File system operations abstraction for dependency injection."""

    @abstractmethod
    def read_file(self, path: Union[str, PathLike[str]]) -> str:
        """Read file contents synchronously."""
        ...

    @abstractmethod
    def write_file(self, path: Union[str, PathLike[str]], content: str) -> None:
        """Write content to file."""
        ...

    @abstractmethod
    def append_file(self, path: Union[str, PathLike[str]], content: str) -> None:
        """Append to existing file."""
        ...

    @abstractmethod
    def exists(self, path: Union[str, PathLike[str]]) -> bool:
        """Check if file/directory exists."""
        ...

    @abstractmethod
    def unlink(self, path: Union[str, PathLike[str]]) -> None:
        """Delete file."""
        ...

    @abstractmethod
    def mkdir(self, path: Union[str, PathLike[str]], exist_ok: bool = False) -> None:
        """Create directory."""
        ...

    @abstractmethod
    def create_read_stream(self, path: Union[str, PathLike[str]]) -> BufferedReader:
        """Create readable stream."""
        ...

    @abstractmethod
    def create_write_stream(self, path: Union[str, PathLike[str]]) -> BufferedWriter:
        """Create writable stream."""
        ...

    @abstractmethod
    def stat(self, path: Union[str, PathLike[str]]) -> stat_result:
        """Get file statistics."""
        ...


class IAuthenticationService(Protocol):
    """OAuth2 authentication service interface for Google APIs."""

    @abstractmethod
    def initialize(self) -> Credentials:
        """Sets up authentication and returns OAuth2 credentials."""
        ...

    @abstractmethod
    def get_auth_url(self) -> str:
        """Generates OAuth2 consent URL."""
        ...

    @abstractmethod
    def get_tokens_from_code(self, code: str) -> AuthTokens:
        """Exchanges auth code for tokens."""
        ...

    @abstractmethod
    def save_tokens(self, tokens: AuthTokens) -> None:
        """Persists tokens to storage."""
        ...

    @abstractmethod
    def load_saved_tokens(self) -> Optional[AuthTokens]:
        """Retrieves saved tokens."""
        ...

    @abstractmethod
    def get_authenticated_client(self) -> Credentials:
        """Returns authenticated OAuth2 credentials."""
        ...


class IGoogleDriveService(Protocol):
    """Google Drive API operations interface."""

    @abstractmethod
    def download_file(
        self, file_id: str, destination_path: str, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """Downloads file from Drive to local filesystem."""
        ...


class IGoogleSheetsService(Protocol):
    """Google Sheets API operations interface."""

    @abstractmethod
    def fetch_spreadsheet_data(self, spreadsheet_id: str, range: str) -> List[List[str]]:
        """Retrieves data from specified spreadsheet range."""
        ...


class IProgressTracker(Protocol):
    """Upload progress tracking and resume capability interface."""

    @abstractmethod
    def load_progress(self) -> UploadProgress:
        """Load saved progress from storage."""
        ...

    @abstractmethod
    def save_progress(self, progress: UploadProgress) -> None:
        """Persist current progress."""
        ...

    @abstractmethod
    def mark_video_processed(self, unique_id: str) -> None:
        """Mark video as successfully uploaded."""
        ...

    @abstractmethod
    def mark_video_failed(self, unique_id: str, error: str) -> None:
        """Record failed upload attempt."""
        ...

    @abstractmethod
    def update_last_processed_row(self, row_number: int) -> None:
        """Update spreadsheet row tracking."""
        ...

    @abstractmethod
    def is_video_processed(self, unique_id: str) -> bool:
        """Check if video already processed."""
        ...

    @abstractmethod
    def get_progress(self) -> UploadProgress:
        """Get current progress state."""
        ...


class IYouTubeService(Protocol):
    """YouTube API operations interface."""

    @abstractmethod
    def upload_video(
        self,
        video_path: str,
        video_data: VideoData,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """Upload video with metadata and optional progress callback."""
        ...


__all__ = [
    "ILogger",
    "IFileOperations",
    "IAuthenticationService",
    "IGoogleDriveService",
    "IGoogleSheetsService",
    "IProgressTracker",
    "IYouTubeService",
]