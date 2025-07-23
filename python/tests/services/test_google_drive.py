"""Tests for GoogleDriveService."""

from io import BytesIO
from unittest.mock import Mock, MagicMock, patch, call

import pytest
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaIoBaseDownload

from interfaces import IFileOperations, ILogger
from services.google_drive import GoogleDriveService


class TestGoogleDriveService:
    """Test GoogleDriveService."""

    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials."""
        return Mock(spec=Credentials)

    @pytest.fixture
    def mock_file_ops(self):
        """Create mock file operations."""
        return Mock(spec=IFileOperations)

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=ILogger)

    @pytest.fixture
    def mock_drive_service(self):
        """Create mock drive service."""
        mock_service = Mock()
        mock_files = Mock()
        mock_service.files.return_value = mock_files
        return mock_service, mock_files

    @pytest.fixture
    @patch("services.google_drive.build")
    def drive_service(
        self, mock_build, mock_credentials, mock_file_ops, mock_logger, mock_drive_service
    ):
        """Create GoogleDriveService instance with mocked dependencies."""
        mock_service, _ = mock_drive_service
        mock_build.return_value = mock_service
        return GoogleDriveService(mock_credentials, mock_file_ops, mock_logger)

    @patch("services.google_drive.build")
    def test_initialization(self, mock_build, mock_credentials, mock_file_ops, mock_logger):
        """Test service initialization."""
        service = GoogleDriveService(mock_credentials, mock_file_ops, mock_logger)
        
        mock_build.assert_called_once_with("drive", "v3", credentials=mock_credentials)
        assert service.service is not None
        assert service.file_operations == mock_file_ops
        assert service.logger == mock_logger

    @patch("services.google_drive.MediaIoBaseDownload")
    def test_download_file_success(
        self, mock_downloader_class, drive_service, mock_drive_service, mock_file_ops, mock_logger
    ):
        """Test successful file download."""
        _, mock_files = mock_drive_service
        
        # Mock file metadata
        mock_files.get.return_value.execute.return_value = {
            "size": "1024",
            "name": "test_video.mp4"
        }
        
        # Mock file download
        mock_media_request = Mock()
        mock_files.get_media.return_value = mock_media_request
        
        # Mock file stream with context manager
        mock_stream = BytesIO()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_stream
        mock_context_manager.__exit__.return_value = None
        mock_file_ops.create_write_stream.return_value = mock_context_manager
        
        # Mock downloader
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.next_chunk.side_effect = [
            (Mock(resumable_progress=512), False),
            (Mock(resumable_progress=1024), True),
        ]
        
        # Test download
        progress_updates = []
        def track_progress(downloaded, total):
            progress_updates.append((downloaded, total))
        
        drive_service.download_file("file123", "/tmp/video.mp4", track_progress)
        
        # Verify metadata fetch
        mock_files.get.assert_called_with(fileId="file123", fields="size,name")
        
        # Verify download request
        mock_files.get_media.assert_called_once_with(fileId="file123")
        
        # Verify file operations
        mock_file_ops.create_write_stream.assert_called_once_with("/tmp/video.mp4")
        
        # Verify progress callbacks
        assert progress_updates == [(512, 1024), (1024, 1024)]
        
        # Verify logging
        assert mock_logger.log.call_count == 2
        mock_logger.log.assert_any_call("Downloading file: test_video.mp4 (1024 bytes)")
        mock_logger.log.assert_any_call("Downloaded file: /tmp/video.mp4")

    @patch("services.google_drive.MediaIoBaseDownload")
    def test_download_file_without_progress_callback(
        self, mock_downloader_class, drive_service, mock_drive_service, mock_file_ops
    ):
        """Test download without progress callback."""
        _, mock_files = mock_drive_service
        
        # Mock file metadata
        mock_files.get.return_value.execute.return_value = {"size": "1024", "name": "test.mp4"}
        
        # Mock file stream with context manager
        mock_stream = BytesIO()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_stream
        mock_context_manager.__exit__.return_value = None
        mock_file_ops.create_write_stream.return_value = mock_context_manager
        
        # Mock downloader
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.next_chunk.return_value = (None, True)
        
        # Test download without callback
        drive_service.download_file("file123", "/tmp/video.mp4")
        
        # Should complete without error
        assert mock_downloader.next_chunk.called

    def test_download_file_metadata_error(self, drive_service, mock_drive_service, mock_logger):
        """Test handling metadata fetch error."""
        _, mock_files = mock_drive_service
        
        # Mock metadata error
        mock_files.get.return_value.execute.side_effect = Exception("Metadata error")
        
        with pytest.raises(Exception, match="Failed to download file file123: Metadata error"):
            drive_service.download_file("file123", "/tmp/video.mp4")
        
        mock_logger.error.assert_called_once()

    @patch("services.google_drive.MediaIoBaseDownload")
    def test_download_file_download_error(
        self, mock_downloader_class, drive_service, mock_drive_service, mock_file_ops, mock_logger
    ):
        """Test handling download error."""
        _, mock_files = mock_drive_service
        
        # Mock file metadata success
        mock_files.get.return_value.execute.return_value = {"size": "1024", "name": "test.mp4"}
        
        # Mock file stream with context manager
        mock_stream = BytesIO()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_stream
        mock_context_manager.__exit__.return_value = None
        mock_file_ops.create_write_stream.return_value = mock_context_manager
        
        # Mock downloader error
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.next_chunk.side_effect = Exception("Download failed")
        
        with pytest.raises(Exception, match="Failed to download file file123: Download failed"):
            drive_service.download_file("file123", "/tmp/video.mp4")
        
        mock_logger.error.assert_called_once()

    @patch("services.google_drive.MediaIoBaseDownload")
    def test_download_file_missing_metadata(
        self, mock_downloader_class, drive_service, mock_drive_service, mock_file_ops, mock_logger
    ):
        """Test handling missing file metadata."""
        _, mock_files = mock_drive_service
        
        # Mock incomplete metadata
        mock_files.get.return_value.execute.return_value = {}
        
        # Mock file stream with context manager
        mock_stream = BytesIO()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_stream
        mock_context_manager.__exit__.return_value = None
        mock_file_ops.create_write_stream.return_value = mock_context_manager
        
        # Mock downloader
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        mock_downloader.next_chunk.return_value = (None, True)
        
        # Should use defaults
        drive_service.download_file("file123", "/tmp/video.mp4")
        
        # Verify logging with defaults
        mock_logger.log.assert_any_call("Downloading file: unknown (0 bytes)")

    @patch("services.google_drive.MediaIoBaseDownload")
    def test_download_large_file_multiple_chunks(
        self, mock_downloader_class, drive_service, mock_drive_service, mock_file_ops
    ):
        """Test downloading large file with multiple chunks."""
        _, mock_files = mock_drive_service
        
        # Mock large file
        mock_files.get.return_value.execute.return_value = {
            "size": "104857600",  # 100MB
            "name": "large_video.mp4"
        }
        
        # Mock file stream with context manager
        mock_stream = BytesIO()
        mock_context_manager = MagicMock()
        mock_context_manager.__enter__.return_value = mock_stream
        mock_context_manager.__exit__.return_value = None
        mock_file_ops.create_write_stream.return_value = mock_context_manager
        
        # Mock multiple chunks
        mock_downloader = Mock()
        mock_downloader_class.return_value = mock_downloader
        
        # Simulate 10 chunks
        chunks = []
        for i in range(10):
            progress = (i + 1) * 10485760  # 10MB chunks
            is_done = i == 9
            chunks.append((Mock(resumable_progress=progress), is_done))
        
        mock_downloader.next_chunk.side_effect = chunks
        
        progress_updates = []
        def track_progress(downloaded, total):
            progress_updates.append((downloaded, total))
        
        drive_service.download_file("file123", "/tmp/large.mp4", track_progress)
        
        # Verify all progress updates
        assert len(progress_updates) == 10
        assert progress_updates[-1] == (104857600, 104857600)

    def test_implements_protocol(self, mock_credentials, mock_file_ops, mock_logger):
        """Test that GoogleDriveService implements IGoogleDriveService protocol."""
        from interfaces import IGoogleDriveService
        
        with patch("services.google_drive.build"):
            service = GoogleDriveService(mock_credentials, mock_file_ops, mock_logger)
            # This would fail at runtime if protocol not satisfied
            _: IGoogleDriveService = service