"""Video processor for downloading and uploading individual videos."""

import os
from typing import Callable, Optional

from interfaces import IFileOperations, IGoogleDriveService, IYouTubeService
from models import Config, VideoData
from utils.drive_utils import extract_file_id_from_drive_link


class VideoProcessor:
    """Processes individual videos: download from Drive, upload to YouTube."""

    def __init__(
        self,
        drive_service: IGoogleDriveService,
        youtube_service: IYouTubeService,
        file_operations: IFileOperations,
        config: Config,
    ) -> None:
        """
        Initialize video processor.

        Args:
            drive_service: Google Drive service for downloads
            youtube_service: YouTube service for uploads
            file_operations: File operations service
            config: Application configuration
        """
        self.drive_service = drive_service
        self.youtube_service = youtube_service
        self.file_operations = file_operations
        self.config = config

    def process_video(
        self,
        video_data: VideoData,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Process a single video: download from Drive and upload to YouTube.

        Args:
            video_data: Video metadata
            progress_callback: Optional callback for progress updates

        Returns:
            YouTube video ID of uploaded video

        Raises:
            ValueError: If Drive link is invalid
            Exception: If download or upload fails
        """
        # Extract file ID from Drive link
        file_id = extract_file_id_from_drive_link(video_data.drive_link)
        if not file_id:
            raise ValueError("Invalid Google Drive link")

        # Ensure temp directory exists
        self.file_operations.mkdir(self.config.temp_dir, exist_ok=True)

        # Create temp file path
        temp_video_path = os.path.join(self.config.temp_dir, f"{video_data.unique_id}.mp4")

        # Download video from Drive
        self.drive_service.download_file(
            file_id, temp_video_path, progress_callback=None
        )

        try:
            # Upload to YouTube
            youtube_id = self.youtube_service.upload_video(
                temp_video_path, video_data, progress_callback=progress_callback
            )

            return youtube_id

        finally:
            # Clean up temp file
            try:
                self.file_operations.unlink(temp_video_path)
            except FileNotFoundError:
                # File already removed, no problem
                pass