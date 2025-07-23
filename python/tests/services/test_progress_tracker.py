"""Tests for ProgressTracker service."""

import json
from unittest.mock import Mock

import pytest

from interfaces import IFileOperations
from models import FailedUpload, UploadProgress
from services.progress_tracker import ProgressTracker


class TestProgressTracker:
    """Test ProgressTracker service."""

    @pytest.fixture
    def mock_file_ops(self):
        """Create mock file operations."""
        mock = Mock(spec=IFileOperations)
        # Default: progress file doesn't exist
        mock.exists.return_value = False
        return mock

    @pytest.fixture
    def tracker(self, mock_file_ops):
        """Create ProgressTracker instance."""
        return ProgressTracker(mock_file_ops, "progress.json")

    def test_load_progress_file_not_exists(self, mock_file_ops):
        """Test loading progress when file doesn't exist."""
        tracker = ProgressTracker(mock_file_ops, "progress.json")

        assert tracker.progress.processed_ids == set()
        assert tracker.progress.last_processed_row == 0
        assert tracker.progress.failed_uploads == []

        # Should not try to read non-existent file
        mock_file_ops.read_file.assert_not_called()

    def test_load_progress_from_file(self, mock_file_ops):
        """Test loading existing progress file."""
        mock_file_ops.exists.return_value = True
        progress_data = {
            "processed_ids": ["id1", "id2"],
            "last_processed_row": 5,
            "failed_uploads": [{"unique_id": "id3", "error": "Failed", "timestamp": "2023-01-01"}],
        }
        mock_file_ops.read_file.return_value = json.dumps(progress_data)

        tracker = ProgressTracker(mock_file_ops, "progress.json")

        assert tracker.progress.processed_ids == {"id1", "id2"}
        assert tracker.progress.last_processed_row == 5
        assert len(tracker.progress.failed_uploads) == 1
        assert tracker.progress.failed_uploads[0].unique_id == "id3"

    def test_load_progress_corrupted_file(self, mock_file_ops):
        """Test loading corrupted progress file returns empty progress."""
        mock_file_ops.exists.return_value = True
        mock_file_ops.read_file.return_value = "invalid json{{"

        tracker = ProgressTracker(mock_file_ops, "progress.json")

        # Should return empty progress on error
        assert tracker.progress.processed_ids == set()
        assert tracker.progress.last_processed_row == 0

    def test_load_progress_read_error(self, mock_file_ops):
        """Test handling read error returns empty progress."""
        mock_file_ops.exists.return_value = True
        mock_file_ops.read_file.side_effect = PermissionError("No read access")

        tracker = ProgressTracker(mock_file_ops, "progress.json")

        # Should return empty progress on error
        assert tracker.progress.processed_ids == set()
        assert tracker.progress.last_processed_row == 0

    def test_save_progress(self, tracker, mock_file_ops):
        """Test saving progress to file."""
        progress = UploadProgress(
            processed_ids={"id1", "id2"},
            last_processed_row=3,
            failed_uploads=[FailedUpload("id3", "Error")],
        )

        tracker.save_progress(progress)

        mock_file_ops.write_file.assert_called_once()
        file_path, content = mock_file_ops.write_file.call_args[0]
        assert file_path == "progress.json"

        # Verify saved content
        saved_data = json.loads(content)
        assert set(saved_data["processed_ids"]) == {"id1", "id2"}
        assert saved_data["last_processed_row"] == 3

    def test_mark_video_processed(self, tracker, mock_file_ops):
        """Test marking video as processed."""
        tracker.mark_video_processed("video123")

        assert "video123" in tracker.progress.processed_ids
        # Should save progress
        mock_file_ops.write_file.assert_called_once()

    def test_mark_video_processed_duplicate(self, tracker, mock_file_ops):
        """Test marking already processed video."""
        tracker.mark_video_processed("video123")
        tracker.mark_video_processed("video123")

        # Set should only have one entry
        assert len(tracker.progress.processed_ids) == 1
        # Should save twice
        assert mock_file_ops.write_file.call_count == 2

    def test_mark_video_failed(self, tracker, mock_file_ops):
        """Test marking video as failed."""
        tracker.mark_video_failed("video123", "Upload error")

        assert len(tracker.progress.failed_uploads) == 1
        failed = tracker.progress.failed_uploads[0]
        assert failed.unique_id == "video123"
        assert failed.error == "Upload error"
        assert failed.timestamp  # Should have timestamp

        # Should save progress
        mock_file_ops.write_file.assert_called_once()

    def test_mark_multiple_failures(self, tracker, mock_file_ops):
        """Test marking multiple failures for same video."""
        tracker.mark_video_failed("video123", "First error")
        tracker.mark_video_failed("video123", "Second error")

        # Should record both failures
        assert len(tracker.progress.failed_uploads) == 2

    def test_update_last_processed_row(self, tracker, mock_file_ops):
        """Test updating last processed row."""
        tracker.update_last_processed_row(10)

        assert tracker.progress.last_processed_row == 10
        mock_file_ops.write_file.assert_called_once()

    def test_is_video_processed(self, tracker):
        """Test checking if video is processed."""
        tracker.mark_video_processed("video123")

        assert tracker.is_video_processed("video123") is True
        assert tracker.is_video_processed("video456") is False

    def test_get_progress(self, tracker):
        """Test getting current progress."""
        tracker.mark_video_processed("id1")
        tracker.mark_video_processed("id2")
        tracker.update_last_processed_row(5)

        progress = tracker.get_progress()

        assert progress.processed_ids == {"id1", "id2"}
        assert progress.last_processed_row == 5

    def test_complex_workflow(self, tracker, mock_file_ops):
        """Test complex progress tracking workflow."""
        # Process some videos
        tracker.mark_video_processed("id1")
        tracker.mark_video_processed("id2")
        tracker.update_last_processed_row(2)

        # Some failures
        tracker.mark_video_failed("id3", "Network error")
        tracker.mark_video_failed("id4", "Invalid format")

        # More successes
        tracker.mark_video_processed("id5")
        tracker.update_last_processed_row(5)

        # Verify final state
        progress = tracker.get_progress()
        assert progress.processed_ids == {"id1", "id2", "id5"}
        assert progress.last_processed_row == 5
        assert len(progress.failed_uploads) == 2

        # Should have saved 7 times (3 processed + 2 failed + 2 row updates)
        assert mock_file_ops.write_file.call_count == 7

    def test_persistence_across_instances(self, mock_file_ops):
        """Test that progress persists across tracker instances."""
        # First tracker
        tracker1 = ProgressTracker(mock_file_ops, "progress.json")
        tracker1.mark_video_processed("id1")
        tracker1.update_last_processed_row(1)

        # Get saved content
        saved_content = mock_file_ops.write_file.call_args[0][1]

        # Second tracker loads the saved progress
        mock_file_ops.exists.return_value = True
        mock_file_ops.read_file.return_value = saved_content

        tracker2 = ProgressTracker(mock_file_ops, "progress.json")

        assert tracker2.is_video_processed("id1") is True
        assert tracker2.progress.last_processed_row == 1

    def test_implements_protocol(self, mock_file_ops):
        """Test that ProgressTracker implements IProgressTracker protocol."""
        from interfaces import IProgressTracker

        tracker = ProgressTracker(mock_file_ops, "progress.json")
        # This would fail at runtime if protocol not satisfied
        _: IProgressTracker = tracker
