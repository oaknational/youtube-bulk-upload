"""Tests for YouTubeBulkUploader."""

import asyncio
from unittest.mock import Mock, patch, AsyncMock

import pytest

from models import Config, UploadProgress, FailedUpload


class TestYouTubeBulkUploader:
    """Test YouTubeBulkUploader orchestrator."""

    @pytest.fixture
    def mock_auth_service(self):
        """Create mock authentication service."""
        from interfaces import IAuthenticationService
        return Mock(spec=IAuthenticationService)

    @pytest.fixture
    def mock_sheets_service(self):
        """Create mock Google Sheets service."""
        from interfaces import IGoogleSheetsService
        return Mock(spec=IGoogleSheetsService)

    @pytest.fixture
    def mock_video_processor(self):
        """Create mock video processor."""
        from core.video_processor import VideoProcessor
        return Mock(spec=VideoProcessor)

    @pytest.fixture
    def mock_progress_tracker(self):
        """Create mock progress tracker."""
        from interfaces import IProgressTracker
        return Mock(spec=IProgressTracker)

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        from interfaces import ILogger
        return Mock(spec=ILogger)

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            client_id="test_client",
            client_secret="test_secret",
            redirect_uri="http://localhost",
            spreadsheet_id="test_sheet_id",
            sheet_range="Sheet1!A:E"
        )

    @pytest.fixture
    def bulk_uploader(
        self, mock_auth_service, mock_sheets_service, mock_video_processor,
        mock_progress_tracker, mock_logger, config
    ):
        """Create YouTubeBulkUploader instance."""
        from core.youtube_bulk_uploader import YouTubeBulkUploader
        return YouTubeBulkUploader(
            auth_service=mock_auth_service,
            sheets_service=mock_sheets_service,
            video_processor=mock_video_processor,
            progress_tracker=mock_progress_tracker,
            logger=mock_logger,
            config=config
        )

    async def test_initialize(self, bulk_uploader, mock_auth_service):
        """Test initialization authenticates."""
        await bulk_uploader.initialize()
        mock_auth_service.initialize.assert_called_once()

    async def test_process_spreadsheet_success(
        self, bulk_uploader, mock_sheets_service, mock_progress_tracker,
        mock_video_processor, mock_logger, config
    ):
        """Test successful spreadsheet processing."""
        # Mock spreadsheet data
        mock_sheets_service.fetch_spreadsheet_data.return_value = [
            ["Header", "Row"],
            ["https://drive.google.com/file/d/123/view", "Video 1", "Desc", "tags", "video1"],
            ["https://drive.google.com/file/d/456/view", "Video 2", "Desc", "tags", "video2"],
        ]
        
        # Mock progress
        mock_progress = UploadProgress(processed_ids=set(), last_processed_row=0)
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock video processing
        mock_video_processor.process_video.side_effect = ["yt_id_1", "yt_id_2"]
        mock_progress_tracker.is_video_processed.return_value = False
        
        # Process with mocked process_video_rows
        with patch("core.youtube_bulk_uploader.process_video_rows") as mock_process_rows:
            mock_process_rows.return_value = asyncio.create_task(asyncio.sleep(0))
            
            await bulk_uploader.process_spreadsheet()
            
            # Verify spreadsheet fetch
            mock_sheets_service.fetch_spreadsheet_data.assert_called_once_with(
                config.spreadsheet_id, config.sheet_range
            )
            
            # Verify process_video_rows was called
            mock_process_rows.assert_called_once()
            call_kwargs = mock_process_rows.call_args[1]
            assert call_kwargs["start_row"] == 1
            assert len(call_kwargs["rows"]) == 3
            
        # Verify final stats logged
        assert any("Upload process completed!" in str(call) for call in mock_logger.log.call_args_list)

    async def test_process_spreadsheet_empty(
        self, bulk_uploader, mock_sheets_service, mock_logger
    ):
        """Test processing empty spreadsheet."""
        mock_sheets_service.fetch_spreadsheet_data.return_value = []
        
        await bulk_uploader.process_spreadsheet()
        
        mock_logger.log.assert_any_call("No data found in spreadsheet")

    async def test_process_spreadsheet_resume(
        self, bulk_uploader, mock_sheets_service, mock_progress_tracker
    ):
        """Test resuming from saved progress."""
        # Mock spreadsheet data
        mock_sheets_service.fetch_spreadsheet_data.return_value = [
            ["Header"],
            ["https://drive.google.com/file/d/123/view", "Video 1", "Desc", "tags", "video1"],
            ["https://drive.google.com/file/d/456/view", "Video 2", "Desc", "tags", "video2"],
        ]
        
        # Mock progress - already processed first video
        mock_progress = UploadProgress(
            processed_ids={"video1"},
            last_processed_row=2
        )
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        with patch("core.youtube_bulk_uploader.process_video_rows") as mock_process_rows:
            mock_process_rows.return_value = asyncio.create_task(asyncio.sleep(0))
            
            await bulk_uploader.process_spreadsheet()
            
            # Should start from row 2 (continuing from last_processed_row)
            call_kwargs = mock_process_rows.call_args[1]
            assert call_kwargs["start_row"] == 2

    async def test_process_spreadsheet_error_handling(
        self, bulk_uploader, mock_sheets_service, mock_logger
    ):
        """Test error handling in spreadsheet processing."""
        mock_sheets_service.fetch_spreadsheet_data.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await bulk_uploader.process_spreadsheet()
        
        mock_logger.error.assert_called_once_with("Fatal error: API Error")

    async def test_retry_failed_uploads(
        self, bulk_uploader, mock_progress_tracker, mock_logger
    ):
        """Test retrying failed uploads."""
        # Mock progress with failed uploads
        failed_uploads = [
            FailedUpload("video1", "Error 1"),
            FailedUpload("video2", "Error 2"),
        ]
        mock_progress = UploadProgress(
            processed_ids={"video1", "video2", "video3"},
            failed_uploads=failed_uploads
        )
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Mock save_progress to track calls
        saved_progress = []
        def save_progress(progress):
            saved_progress.append(progress.copy() if hasattr(progress, 'copy') else progress)
        mock_progress_tracker.save_progress.side_effect = save_progress
        
        with patch.object(bulk_uploader, 'process_spreadsheet') as mock_process:
            mock_process.return_value = asyncio.create_task(asyncio.sleep(0))
            
            await bulk_uploader.retry_failed_uploads()
            
            # Verify failed uploads were cleared
            assert len(saved_progress) >= 1
            first_save = saved_progress[0]
            assert len(first_save.failed_uploads) == 0
            
            # Verify videos were removed from processed list
            assert "video1" not in first_save.processed_ids
            assert "video2" not in first_save.processed_ids
            assert "video3" in first_save.processed_ids
            
            # Verify process_spreadsheet was called
            mock_process.assert_called_once()
            
            # Verify logging
            mock_logger.log.assert_any_call("Retrying 2 failed uploads...")

    async def test_log_final_stats(self, bulk_uploader, mock_progress_tracker, mock_logger):
        """Test final statistics logging."""
        mock_progress = UploadProgress(
            processed_ids={"video1", "video2", "video3"},
            failed_uploads=[FailedUpload("video4", "Error")]
        )
        mock_progress_tracker.get_progress.return_value = mock_progress
        
        # Call private method directly for testing
        bulk_uploader._log_final_stats()
        
        mock_logger.log.assert_any_call("Upload process completed!")
        mock_logger.log.assert_any_call("Total processed: 3")
        mock_logger.log.assert_any_call("Failed uploads: 1")