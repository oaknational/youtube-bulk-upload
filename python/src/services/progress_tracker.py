"""Progress tracker service implementation."""

from interfaces import IFileOperations, IProgressTracker
from models import FailedUpload, UploadProgress
from utils.progress_serializer import deserialize_progress, serialize_progress


class ProgressTracker(IProgressTracker):
    """Progress tracking implementation with file persistence."""

    def __init__(self, file_operations: IFileOperations, progress_file: str) -> None:
        """
        Initialize progress tracker.

        Args:
            file_operations: File operations service
            progress_file: Path to progress file
        """
        self.file_operations = file_operations
        self.progress_file = progress_file
        self.progress = self.load_progress()

    def load_progress(self) -> UploadProgress:
        """
        Load saved progress from storage.

        Returns:
            Loaded progress or empty progress if file doesn't exist
        """
        if not self.file_operations.exists(self.progress_file):
            return UploadProgress()

        try:
            content = self.file_operations.read_file(self.progress_file)
            return deserialize_progress(content)
        except Exception:
            # Return empty progress on any error
            return UploadProgress()

    def save_progress(self, progress: UploadProgress) -> None:
        """
        Persist current progress.

        Args:
            progress: Progress to save
        """
        serialized = serialize_progress(progress)
        self.file_operations.write_file(self.progress_file, serialized)

    def mark_video_processed(self, unique_id: str) -> None:
        """
        Mark video as successfully uploaded.

        Args:
            unique_id: Video unique ID
        """
        self.progress.processed_ids.add(unique_id)
        self.save_progress(self.progress)

    def mark_video_failed(self, unique_id: str, error: str) -> None:
        """
        Record failed upload attempt.

        Args:
            unique_id: Video unique ID
            error: Error message
        """
        failed = FailedUpload(unique_id=unique_id, error=error)
        self.progress.failed_uploads.append(failed)
        self.save_progress(self.progress)

    def update_last_processed_row(self, row_number: int) -> None:
        """
        Update spreadsheet row tracking.

        Args:
            row_number: Last processed row number
        """
        self.progress.last_processed_row = row_number
        self.save_progress(self.progress)

    def is_video_processed(self, unique_id: str) -> bool:
        """
        Check if video already processed.

        Args:
            unique_id: Video unique ID

        Returns:
            True if already processed
        """
        return unique_id in self.progress.processed_ids

    def get_progress(self) -> UploadProgress:
        """
        Get current progress state.

        Returns:
            Current progress
        """
        return self.progress
