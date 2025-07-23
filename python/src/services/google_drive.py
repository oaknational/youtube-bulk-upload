"""Google Drive service implementation."""

from typing import Callable, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from interfaces import IFileOperations, IGoogleDriveService, ILogger


class GoogleDriveService(IGoogleDriveService):
    """Google Drive API operations implementation."""

    def __init__(
        self,
        credentials: Credentials,
        file_operations: IFileOperations,
        logger: ILogger,
    ) -> None:
        """
        Initialize Google Drive service.

        Args:
            credentials: Authenticated Google credentials
            file_operations: File operations service
            logger: Logger service
        """
        self.service = build("drive", "v3", credentials=credentials)
        self.file_operations = file_operations
        self.logger = logger

    def download_file(
        self,
        file_id: str,
        destination_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Downloads file from Drive to local filesystem.

        Args:
            file_id: Google Drive file ID
            destination_path: Local path to save the file
            progress_callback: Optional callback for progress updates (bytes_downloaded, total_bytes)

        Raises:
            Exception: If download fails
        """
        try:
            # Get file metadata first to know the size
            file_metadata = self.service.files().get(fileId=file_id, fields="size,name").execute()
            file_size = int(file_metadata.get("size", 0))
            file_name = file_metadata.get("name", "unknown")

            self.logger.log(f"Downloading file: {file_name} ({file_size} bytes)")

            # Download the file
            request = self.service.files().get_media(fileId=file_id)
            
            with self.file_operations.create_write_stream(destination_path) as fh:
                downloader = MediaIoBaseDownload(fh, request)
                
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status and progress_callback:
                        bytes_downloaded = int(status.resumable_progress)
                        progress_callback(bytes_downloaded, file_size)

            self.logger.log(f"Downloaded file: {destination_path}")

        except Exception as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            raise Exception(f"Failed to download file {file_id}: {str(e)}") from e