"""Tests for service interface protocols."""

from io import BufferedReader, BufferedWriter
from os import PathLike, stat_result
from typing import Optional, Union
from unittest.mock import Mock, MagicMock

import pytest
from google.oauth2.credentials import Credentials

from src.interfaces import (
    IAuthenticationService,
    IFileOperations,
    IGoogleDriveService,
    IGoogleSheetsService,
    ILogger,
    IProgressTracker,
    IYouTubeService,
)
from src.types import AuthTokens, UploadProgress, VideoData, FailedUpload


class TestILogger:
    """Test ILogger protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that a mock can implement ILogger protocol."""

        class MockLogger:
            def log(self, message: str) -> None:
                pass

            def error(self, message: str) -> None:
                pass

            def warn(self, message: str) -> None:
                pass

        logger: ILogger = MockLogger()
        logger.log("test")
        logger.error("error")
        logger.warn("warning")

    def test_mock_logger(self) -> None:
        """Test using Mock to implement ILogger."""
        logger = Mock(spec=ILogger)
        logger.log("info message")
        logger.error("error message")
        logger.warn("warning message")

        logger.log.assert_called_once_with("info message")
        logger.error.assert_called_once_with("error message")
        logger.warn.assert_called_once_with("warning message")


class TestIFileOperations:
    """Test IFileOperations protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that a class can implement IFileOperations protocol."""

        class MockFileOps:
            def read_file(self, path: Union[str, PathLike[str]]) -> str:
                return "content"

            def write_file(self, path: Union[str, PathLike[str]], content: str) -> None:
                pass

            def append_file(self, path: Union[str, PathLike[str]], content: str) -> None:
                pass

            def exists(self, path: Union[str, PathLike[str]]) -> bool:
                return True

            def unlink(self, path: Union[str, PathLike[str]]) -> None:
                pass

            def mkdir(self, path: Union[str, PathLike[str]], exist_ok: bool = False) -> None:
                pass

            def create_read_stream(self, path: Union[str, PathLike[str]]) -> BufferedReader:
                return Mock(spec=BufferedReader)

            def create_write_stream(self, path: Union[str, PathLike[str]]) -> BufferedWriter:
                return Mock(spec=BufferedWriter)

            def stat(self, path: Union[str, PathLike[str]]) -> stat_result:
                return Mock(spec=stat_result)

        file_ops: IFileOperations = MockFileOps()
        assert file_ops.read_file("test.txt") == "content"
        assert file_ops.exists("test.txt") is True

    def test_mock_file_operations(self) -> None:
        """Test using Mock to implement IFileOperations."""
        file_ops = Mock(spec=IFileOperations)
        file_ops.read_file.return_value = "file content"
        file_ops.exists.return_value = False

        content = file_ops.read_file("test.txt")
        exists = file_ops.exists("test.txt")

        assert content == "file content"
        assert exists is False
        file_ops.read_file.assert_called_once_with("test.txt")
        file_ops.exists.assert_called_once_with("test.txt")


class TestIAuthenticationService:
    """Test IAuthenticationService protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that a class can implement IAuthenticationService protocol."""

        class MockAuth:
            def initialize(self) -> Credentials:
                return Mock(spec=Credentials)

            def get_auth_url(self) -> str:
                return "https://accounts.google.com/oauth/authorize"

            def get_tokens_from_code(self, code: str) -> AuthTokens:
                return AuthTokens(access_token="access", refresh_token="refresh")

            def save_tokens(self, tokens: AuthTokens) -> None:
                pass

            def load_saved_tokens(self) -> Optional[AuthTokens]:
                return None

            def get_authenticated_client(self) -> Credentials:
                return Mock(spec=Credentials)

        auth: IAuthenticationService = MockAuth()
        assert isinstance(auth.initialize(), Mock)
        assert auth.get_auth_url().startswith("https://")

    def test_mock_authentication_service(self) -> None:
        """Test using Mock to implement IAuthenticationService."""
        auth = Mock(spec=IAuthenticationService)
        mock_creds = Mock(spec=Credentials)
        auth.initialize.return_value = mock_creds
        auth.get_auth_url.return_value = "https://oauth.url"
        auth.load_saved_tokens.return_value = None

        creds = auth.initialize()
        url = auth.get_auth_url()
        tokens = auth.load_saved_tokens()

        assert creds == mock_creds
        assert url == "https://oauth.url"
        assert tokens is None


class TestIGoogleDriveService:
    """Test IGoogleDriveService protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that a class can implement IGoogleDriveService protocol."""

        class MockDrive:
            def download_file(
                self, file_id: str, destination_path: str, progress_callback=None
            ) -> None:
                if progress_callback:
                    progress_callback(50, 100)

        drive: IGoogleDriveService = MockDrive()
        drive.download_file("file123", "/tmp/video.mp4")

    def test_mock_drive_service(self) -> None:
        """Test using Mock to implement IGoogleDriveService."""
        drive = Mock(spec=IGoogleDriveService)

        progress_cb = Mock()
        drive.download_file("file123", "/tmp/video.mp4", progress_cb)

        drive.download_file.assert_called_once_with("file123", "/tmp/video.mp4", progress_cb)


class TestIGoogleSheetsService:
    """Test IGoogleSheetsService protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that a class can implement IGoogleSheetsService protocol."""

        class MockSheets:
            def fetch_spreadsheet_data(self, spreadsheet_id: str, range: str) -> list:
                return [["col1", "col2"], ["val1", "val2"]]

        sheets: IGoogleSheetsService = MockSheets()
        data = sheets.fetch_spreadsheet_data("sheet123", "A1:B2")
        assert len(data) == 2

    def test_mock_sheets_service(self) -> None:
        """Test using Mock to implement IGoogleSheetsService."""
        sheets = Mock(spec=IGoogleSheetsService)
        sheets.fetch_spreadsheet_data.return_value = [["a", "b"], ["c", "d"]]

        data = sheets.fetch_spreadsheet_data("sheet123", "A:B")

        assert data == [["a", "b"], ["c", "d"]]
        sheets.fetch_spreadsheet_data.assert_called_once_with("sheet123", "A:B")


class TestIProgressTracker:
    """Test IProgressTracker protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that a class can implement IProgressTracker protocol."""

        class MockTracker:
            def __init__(self):
                self.progress = UploadProgress()

            def load_progress(self) -> UploadProgress:
                return self.progress

            def save_progress(self, progress: UploadProgress) -> None:
                self.progress = progress

            def mark_video_processed(self, unique_id: str) -> None:
                self.progress.processed_ids.add(unique_id)

            def mark_video_failed(self, unique_id: str, error: str) -> None:
                self.progress.failed_uploads.append(FailedUpload(unique_id, error))

            def update_last_processed_row(self, row_number: int) -> None:
                self.progress.last_processed_row = row_number

            def is_video_processed(self, unique_id: str) -> bool:
                return unique_id in self.progress.processed_ids

            def get_progress(self) -> UploadProgress:
                return self.progress

        tracker: IProgressTracker = MockTracker()
        tracker.mark_video_processed("video123")
        assert tracker.is_video_processed("video123")

    def test_mock_progress_tracker(self) -> None:
        """Test using Mock to implement IProgressTracker."""
        tracker = Mock(spec=IProgressTracker)
        mock_progress = UploadProgress()
        tracker.load_progress.return_value = mock_progress
        tracker.is_video_processed.return_value = True

        progress = tracker.load_progress()
        processed = tracker.is_video_processed("video123")

        assert progress == mock_progress
        assert processed is True
        tracker.mark_video_processed("video456")
        tracker.mark_video_processed.assert_called_once_with("video456")


class TestIYouTubeService:
    """Test IYouTubeService protocol."""

    def test_protocol_implementation(self) -> None:
        """Test that a class can implement IYouTubeService protocol."""

        class MockYouTube:
            def upload_video(
                self, video_path: str, video_data: VideoData, progress_callback=None
            ) -> str:
                if progress_callback:
                    progress_callback(100, 100)
                return "video_id_123"

        youtube: IYouTubeService = MockYouTube()
        video_data = VideoData(
            drive_link="https://drive.google.com/file/d/123",
            title="Test",
            description="Desc",
            tags=["tag1"],
            unique_id="uid123",
        )
        video_id = youtube.upload_video("/tmp/video.mp4", video_data)
        assert video_id == "video_id_123"

    def test_mock_youtube_service(self) -> None:
        """Test using Mock to implement IYouTubeService."""
        youtube = Mock(spec=IYouTubeService)
        youtube.upload_video.return_value = "uploaded_video_id"

        video_data = VideoData(
            drive_link="https://drive.google.com/file/d/123",
            title="Test Video",
            description="Test Description",
            tags=["test"],
            unique_id="unique123",
        )
        progress_cb = Mock()

        video_id = youtube.upload_video("/tmp/video.mp4", video_data, progress_cb)

        assert video_id == "uploaded_video_id"
        youtube.upload_video.assert_called_once_with("/tmp/video.mp4", video_data, progress_cb)


class TestProtocolInteraction:
    """Test interaction between multiple protocols."""

    def test_service_composition(self) -> None:
        """Test that services can work together through protocols."""
        # Create mocks for all services
        logger = Mock(spec=ILogger)
        file_ops = Mock(spec=IFileOperations)
        tracker = Mock(spec=IProgressTracker)
        youtube = Mock(spec=IYouTubeService)

        # Setup return values
        file_ops.exists.return_value = True
        tracker.is_video_processed.return_value = False
        youtube.upload_video.return_value = "video123"

        # Simulate a workflow
        video_data = VideoData(
            drive_link="https://drive.google.com/file/d/123",
            title="Test",
            description="Desc",
            tags=["tag"],
            unique_id="uid123",
        )

        if not tracker.is_video_processed(video_data.unique_id):
            logger.log(f"Processing video: {video_data.title}")
            if file_ops.exists("/tmp/video.mp4"):
                video_id = youtube.upload_video("/tmp/video.mp4", video_data)
                tracker.mark_video_processed(video_data.unique_id)
                logger.log(f"Uploaded video: {video_id}")

        # Verify interactions
        tracker.is_video_processed.assert_called_with("uid123")
        logger.log.assert_any_call("Processing video: Test")
        file_ops.exists.assert_called_with("/tmp/video.mp4")
        youtube.upload_video.assert_called_once()
        tracker.mark_video_processed.assert_called_with("uid123")