"""Tests for spreadsheet processor."""

import asyncio
from unittest.mock import Mock, call

import pytest

from models import VideoData


class TestSpreadsheetProcessor:
    """Test spreadsheet processing logic."""

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        from interfaces import ILogger
        return Mock(spec=ILogger)

    @pytest.fixture
    def mock_progress_tracker(self):
        """Create mock progress tracker."""
        from interfaces import IProgressTracker
        return Mock(spec=IProgressTracker)

    @pytest.fixture
    def mock_video_processor(self):
        """Create mock video processor."""
        from core.video_processor import VideoProcessor
        return Mock(spec=VideoProcessor)

    @pytest.fixture
    def sample_rows(self):
        """Create sample spreadsheet rows."""
        return [
            ["Header", "Row", "Ignored"],  # Header row
            ["https://drive.google.com/file/d/123/view", "Video 1", "Description 1", "tag1,tag2", "video1"],
            ["https://drive.google.com/file/d/456/view", "Video 2", "Description 2", "tag3,tag4", "video2"],
            ["https://drive.google.com/file/d/789/view", "Video 3", "Description 3", "tag5", "video3"],
        ]

    async def test_process_video_rows_success(
        self, mock_logger, mock_progress_tracker, mock_video_processor, sample_rows
    ):
        """Test successful processing of video rows."""
        from core.spreadsheet_processor import process_video_rows
        
        # Mock video processor to return YouTube IDs
        mock_video_processor.process_video.side_effect = ["yt_id_1", "yt_id_2", "yt_id_3"]
        
        # Mock progress tracker - nothing processed yet
        mock_progress_tracker.is_video_processed.return_value = False
        
        # Process rows starting from row 1 (skip header)
        await process_video_rows(
            rows=sample_rows,
            start_row=1,
            logger=mock_logger,
            progress_tracker=mock_progress_tracker,
            video_processor=mock_video_processor,
        )
        
        # Verify all videos were processed
        assert mock_video_processor.process_video.call_count == 3
        
        # Verify progress tracking
        assert mock_progress_tracker.mark_video_processed.call_count == 3
        mock_progress_tracker.mark_video_processed.assert_any_call("video1")
        mock_progress_tracker.mark_video_processed.assert_any_call("video2")
        mock_progress_tracker.mark_video_processed.assert_any_call("video3")
        
        # Verify row updates
        assert mock_progress_tracker.update_last_processed_row.call_count == 3
        mock_progress_tracker.update_last_processed_row.assert_any_call(2)
        mock_progress_tracker.update_last_processed_row.assert_any_call(3)
        mock_progress_tracker.update_last_processed_row.assert_any_call(4)
        
        # Verify logging
        assert mock_logger.log.call_count >= 3
        mock_logger.log.assert_any_call("Processing video 2/4: video1")

    async def test_process_video_rows_skip_processed(
        self, mock_logger, mock_progress_tracker, mock_video_processor, sample_rows
    ):
        """Test skipping already processed videos."""
        from core.spreadsheet_processor import process_video_rows
        
        # Mock first video as already processed
        mock_progress_tracker.is_video_processed.side_effect = [True, False, False]
        mock_video_processor.process_video.side_effect = ["yt_id_2", "yt_id_3"]
        
        await process_video_rows(
            rows=sample_rows,
            start_row=1,
            logger=mock_logger,
            progress_tracker=mock_progress_tracker,
            video_processor=mock_video_processor,
        )
        
        # Should only process 2 videos
        assert mock_video_processor.process_video.call_count == 2
        
        # Should log skip
        mock_logger.log.assert_any_call("Skipping already processed video: video1")

    async def test_process_video_rows_with_failures(
        self, mock_logger, mock_progress_tracker, mock_video_processor, sample_rows
    ):
        """Test handling of processing failures."""
        from core.spreadsheet_processor import process_video_rows
        
        # Mock second video to fail
        mock_video_processor.process_video.side_effect = [
            "yt_id_1",
            Exception("Upload failed"),
            "yt_id_3"
        ]
        mock_progress_tracker.is_video_processed.return_value = False
        
        await process_video_rows(
            rows=sample_rows,
            start_row=1,
            logger=mock_logger,
            progress_tracker=mock_progress_tracker,
            video_processor=mock_video_processor,
        )
        
        # All videos should be attempted
        assert mock_video_processor.process_video.call_count == 3
        
        # Two should succeed
        assert mock_progress_tracker.mark_video_processed.call_count == 2
        
        # One should fail
        mock_progress_tracker.mark_video_failed.assert_called_once_with(
            "video2", "Upload failed"
        )
        
        # Error should be logged
        mock_logger.error.assert_called_once_with(
            "Failed to process video2: Upload failed"
        )

    async def test_process_video_rows_empty_rows(
        self, mock_logger, mock_progress_tracker, mock_video_processor
    ):
        """Test handling of empty rows."""
        from core.spreadsheet_processor import process_video_rows
        
        rows = [
            ["Header"],
            ["https://drive.google.com/file/d/123/view", "Video 1", "Desc", "tags", "video1"],
            [],  # Empty row
            None,  # None row
            ["https://drive.google.com/file/d/456/view", "Video 2", "Desc", "tags", "video2"],
        ]
        
        mock_progress_tracker.is_video_processed.return_value = False
        mock_video_processor.process_video.side_effect = ["yt_id_1", "yt_id_2"]
        
        await process_video_rows(
            rows=rows,
            start_row=1,
            logger=mock_logger,
            progress_tracker=mock_progress_tracker,
            video_processor=mock_video_processor,
        )
        
        # Should process only 2 valid videos
        assert mock_video_processor.process_video.call_count == 2
        
        # Should log empty rows
        mock_logger.log.assert_any_call("Row 3 is empty, skipping")
        mock_logger.log.assert_any_call("Row 4 is empty, skipping")

    async def test_process_video_rows_invalid_data(
        self, mock_logger, mock_progress_tracker, mock_video_processor
    ):
        """Test handling of invalid row data."""
        from core.spreadsheet_processor import process_video_rows
        
        rows = [
            ["Header"],
            ["https://drive.google.com/file/d/123/view", "Video 1", "Desc", "tags", "video1"],
            ["not_a_drive_link", "Invalid", "Desc", "tags", "invalid"],  # Invalid link - will fail in processor
            ["https://drive.google.com/file/d/456/view"],  # Missing columns
        ]
        
        mock_progress_tracker.is_video_processed.return_value = False
        # First video succeeds, second fails due to invalid link
        mock_video_processor.process_video.side_effect = [
            "yt_id_1",
            ValueError("Invalid Google Drive link")
        ]
        
        await process_video_rows(
            rows=rows,
            start_row=1,
            logger=mock_logger,
            progress_tracker=mock_progress_tracker,
            video_processor=mock_video_processor,
        )
        
        # Should attempt to process 2 videos (third row has missing columns)
        assert mock_video_processor.process_video.call_count == 2
        
        # Should log invalid data for row with missing columns
        assert any("invalid data" in str(call) for call in mock_logger.log.call_args_list)
        
        # Should mark the invalid link video as failed
        mock_progress_tracker.mark_video_failed.assert_called_once_with(
            "invalid", "Invalid Google Drive link"
        )

    async def test_process_video_rows_resume_from_middle(
        self, mock_logger, mock_progress_tracker, mock_video_processor, sample_rows
    ):
        """Test resuming from middle of spreadsheet."""
        from core.spreadsheet_processor import process_video_rows
        
        mock_progress_tracker.is_video_processed.return_value = False
        mock_video_processor.process_video.side_effect = ["yt_id_2", "yt_id_3"]
        
        # Start from row 2 (third row, 0-indexed)
        await process_video_rows(
            rows=sample_rows,
            start_row=2,
            logger=mock_logger,
            progress_tracker=mock_progress_tracker,
            video_processor=mock_video_processor,
        )
        
        # Should only process last 2 videos
        assert mock_video_processor.process_video.call_count == 2
        
        # Should update rows 3 and 4
        calls = mock_progress_tracker.update_last_processed_row.call_args_list
        assert calls[0] == call(3)
        assert calls[1] == call(4)

    async def test_process_video_rows_rate_limiting(
        self, mock_logger, mock_progress_tracker, mock_video_processor, sample_rows, monkeypatch
    ):
        """Test rate limiting between videos."""
        from core.spreadsheet_processor import process_video_rows
        
        mock_progress_tracker.is_video_processed.return_value = False
        mock_video_processor.process_video.return_value = "yt_id"
        
        # Track sleep calls
        sleep_calls = []
        
        async def mock_sleep(seconds):
            sleep_calls.append(seconds)
        
        monkeypatch.setattr(asyncio, "sleep", mock_sleep)
        
        await process_video_rows(
            rows=sample_rows,
            start_row=1,
            logger=mock_logger,
            progress_tracker=mock_progress_tracker,
            video_processor=mock_video_processor,
        )
        
        # Should have delays between videos (3 videos = 3 delays)
        assert len(sleep_calls) == 3
        assert all(delay == 2 for delay in sleep_calls)