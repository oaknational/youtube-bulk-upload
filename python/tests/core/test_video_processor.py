"""Tests for VideoProcessor."""

import os
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

from models import Config, VideoData


class TestVideoProcessor:
    """Test VideoProcessor core component."""

    @pytest.fixture
    def mock_drive_service(self):
        """Create mock Google Drive service."""
        from interfaces import IGoogleDriveService
        return Mock(spec=IGoogleDriveService)

    @pytest.fixture
    def mock_youtube_service(self):
        """Create mock YouTube service."""
        from interfaces import IYouTubeService
        return Mock(spec=IYouTubeService)

    @pytest.fixture
    def mock_file_ops(self):
        """Create mock file operations."""
        from interfaces import IFileOperations
        return Mock(spec=IFileOperations)

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost",
            spreadsheet_id="test_sheet",
            temp_dir="/tmp/test_videos"
        )

    @pytest.fixture
    def sample_video_data(self):
        """Create sample video data."""
        return VideoData(
            drive_link="https://drive.google.com/file/d/1234567890/view",
            title="Test Video",
            description="Test Description",
            tags=["test", "video"],
            unique_id="unique123"
        )

    @pytest.fixture
    def video_processor(self, mock_drive_service, mock_youtube_service, mock_file_ops, config):
        """Create VideoProcessor instance."""
        from core.video_processor import VideoProcessor
        return VideoProcessor(
            drive_service=mock_drive_service,
            youtube_service=mock_youtube_service,
            file_operations=mock_file_ops,
            config=config
        )

    def test_process_video_success(
        self, video_processor, mock_drive_service, mock_youtube_service, 
        mock_file_ops, sample_video_data, config
    ):
        """Test successful video processing."""
        # Mock YouTube upload to return an ID
        mock_youtube_service.upload_video.return_value = "youtube_id_123"
        
        # Process video
        result = video_processor.process_video(sample_video_data)
        
        # Verify result
        assert result == "youtube_id_123"
        
        # Verify temp directory was created
        mock_file_ops.mkdir.assert_called_once_with(config.temp_dir, exist_ok=True)
        
        # Verify download was called
        expected_temp_path = os.path.join(config.temp_dir, "unique123.mp4")
        mock_drive_service.download_file.assert_called_once_with(
            "1234567890", 
            expected_temp_path,
            progress_callback=None
        )
        
        # Verify upload was called
        assert mock_youtube_service.upload_video.called
        call_args = mock_youtube_service.upload_video.call_args
        assert call_args[0][0] == expected_temp_path
        assert call_args[0][1] == sample_video_data
        
        # Verify cleanup
        mock_file_ops.unlink.assert_called_once_with(expected_temp_path)

    def test_process_video_with_progress_callback(
        self, video_processor, mock_youtube_service, sample_video_data
    ):
        """Test video processing with progress callbacks."""
        mock_youtube_service.upload_video.return_value = "youtube_id_123"
        
        # Track progress updates
        progress_updates = []
        def track_progress(current, total):
            progress_updates.append((current, total))
        
        # Process with callback
        result = video_processor.process_video(sample_video_data, track_progress)
        
        assert result == "youtube_id_123"
        
        # Verify upload callback was passed
        upload_call = mock_youtube_service.upload_video.call_args
        assert upload_call[1]["progress_callback"] is not None

    def test_process_video_invalid_drive_link(
        self, video_processor, sample_video_data
    ):
        """Test processing with invalid Drive link."""
        sample_video_data.drive_link = "not_a_valid_link"
        
        with pytest.raises(ValueError, match="Invalid Google Drive link"):
            video_processor.process_video(sample_video_data)

    def test_process_video_download_failure(
        self, video_processor, mock_drive_service, mock_file_ops, sample_video_data
    ):
        """Test handling download failure."""
        # Mock download failure
        mock_drive_service.download_file.side_effect = Exception("Download failed")
        
        with pytest.raises(Exception, match="Download failed"):
            video_processor.process_video(sample_video_data)
        
        # Verify no cleanup attempted
        mock_file_ops.unlink.assert_not_called()

    def test_process_video_upload_failure_with_cleanup(
        self, video_processor, mock_youtube_service, mock_file_ops, 
        sample_video_data, config
    ):
        """Test that temp file is cleaned up even on upload failure."""
        # Mock upload failure
        mock_youtube_service.upload_video.side_effect = Exception("Upload failed")
        
        # Process should raise but still cleanup
        with pytest.raises(Exception, match="Upload failed"):
            video_processor.process_video(sample_video_data)
        
        # Verify cleanup was attempted
        expected_temp_path = os.path.join(config.temp_dir, "unique123.mp4")
        mock_file_ops.unlink.assert_called_once_with(expected_temp_path)

    def test_process_video_custom_temp_dir(
        self, mock_drive_service, mock_youtube_service, mock_file_ops, sample_video_data
    ):
        """Test using custom temp directory."""
        # Create config with different temp dir
        custom_config = Config(
            client_id="test",
            client_secret="test",
            redirect_uri="http://localhost",
            spreadsheet_id="test",
            temp_dir="/custom/temp"
        )
        
        from core.video_processor import VideoProcessor
        processor = VideoProcessor(
            mock_drive_service,
            mock_youtube_service,
            mock_file_ops,
            custom_config
        )
        
        mock_youtube_service.upload_video.return_value = "youtube_123"
        
        processor.process_video(sample_video_data)
        
        # Verify custom temp dir was used
        mock_file_ops.mkdir.assert_called_once_with("/custom/temp", exist_ok=True)
        expected_path = os.path.join("/custom/temp", "unique123.mp4")
        mock_drive_service.download_file.assert_called_once_with(
            "1234567890", expected_path, progress_callback=None
        )

    def test_process_video_file_not_cleaned_if_not_exists(
        self, video_processor, mock_youtube_service, mock_file_ops, sample_video_data
    ):
        """Test that missing files don't cause cleanup errors."""
        mock_youtube_service.upload_video.return_value = "youtube_123"
        
        # Mock file doesn't exist during cleanup
        mock_file_ops.unlink.side_effect = FileNotFoundError()
        
        # Should not raise
        result = video_processor.process_video(sample_video_data)
        assert result == "youtube_123"