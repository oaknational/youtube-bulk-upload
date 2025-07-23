"""YouTube service implementation."""

from typing import Callable, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from interfaces import IFileOperations, IYouTubeService
from models import VideoData


class YouTubeService(IYouTubeService):
    """YouTube API operations implementation."""

    def __init__(
        self,
        credentials: Credentials,
        file_operations: IFileOperations,
    ) -> None:
        """
        Initialize YouTube service.

        Args:
            credentials: Authenticated Google credentials
            file_operations: File operations service
        """
        self.service = build("youtube", "v3", credentials=credentials)
        self.file_operations = file_operations

    def upload_video(
        self,
        video_path: str,
        video_data: VideoData,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Upload video with metadata and optional progress callback.

        Args:
            video_path: Path to video file
            video_data: Video metadata
            progress_callback: Optional callback for progress updates (bytes_uploaded, total_bytes)

        Returns:
            YouTube video ID of uploaded video

        Raises:
            Exception: If upload fails
        """
        try:
            # Get file size for progress tracking
            file_stat = self.file_operations.stat(video_path)
            file_size = file_stat.st_size

            # Prepare the upload
            body = {
                "snippet": {
                    "title": video_data.title,
                    "description": video_data.description,
                    "tags": video_data.tags,
                    "categoryId": "22",  # People & Blogs
                },
                "status": {
                    "privacyStatus": "private",
                    "selfDeclaredMadeForKids": False,
                },
            }

            # Create media upload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload in a single request
                resumable=True,
                mimetype="video/*",
            )

            # Insert video
            request = self.service.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media,
            )

            # Execute upload with progress tracking
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status and progress_callback:
                    bytes_uploaded = int(status.resumable_progress)
                    progress_callback(bytes_uploaded, file_size)

            # Return the video ID
            video_id = response.get("id", "")
            if not video_id:
                raise Exception("Upload succeeded but no video ID returned")

            return video_id

        except Exception as e:
            raise Exception(f"Failed to upload video: {str(e)}") from e