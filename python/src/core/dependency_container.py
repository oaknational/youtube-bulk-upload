"""Dependency injection container for assembling services."""

from models import Config
from services import (
    AuthenticationService,
    FileOperations,
    GoogleDriveService,
    GoogleSheetsService,
    Logger,
    ProgressTracker,
    YouTubeService,
)

from .video_processor import VideoProcessor
from .youtube_bulk_uploader import YouTubeBulkUploader


class DependencyContainer:
    """Container for managing and injecting dependencies."""

    def __init__(self, config: Config) -> None:
        """
        Initialize dependency container.

        Args:
            config: Application configuration
        """
        self.config = config
        
        # Initialize basic services
        self.file_operations = FileOperations()
        self.logger = Logger(self.file_operations, config.log_file)
        self.progress_tracker = ProgressTracker(self.file_operations, config.progress_file)
        
        # Authentication service (needs to be initialized before Google services)
        self.auth_service = AuthenticationService(
            config, self.file_operations, self.logger
        )

    def create_youtube_bulk_uploader(self) -> YouTubeBulkUploader:
        """
        Create and return a fully configured YouTubeBulkUploader instance.

        Returns:
            Configured YouTubeBulkUploader ready to process videos
        """
        # Initialize authentication and get credentials
        credentials = self.auth_service.initialize()
        
        # Create Google API services with authenticated credentials
        sheets_service = GoogleSheetsService(credentials)
        drive_service = GoogleDriveService(
            credentials, self.file_operations, self.logger
        )
        youtube_service = YouTubeService(credentials, self.file_operations)
        
        # Create video processor
        video_processor = VideoProcessor(
            drive_service, youtube_service, self.file_operations, self.config
        )
        
        # Create and return the main uploader
        return YouTubeBulkUploader(
            auth_service=self.auth_service,
            sheets_service=sheets_service,
            video_processor=video_processor,
            progress_tracker=self.progress_tracker,
            logger=self.logger,
            config=self.config,
        )