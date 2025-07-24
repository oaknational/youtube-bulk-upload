"""Service interfaces (Protocols) for dependency injection."""

from abc import abstractmethod
from io import BufferedReader, BufferedWriter
from os import PathLike, stat_result
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Union

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload

from models import AuthTokens, UploadProgress, VideoData


class ILogger(Protocol):
    """
    Logging operations interface for standardized application logging.
    
    This protocol defines the contract for logging services used throughout
    the application. Implementations should handle log persistence, formatting,
    and optional features like log rotation.
    
    Example:
        >>> logger: ILogger = Logger(file_operations, "upload.log")
        >>> logger.log("Starting video upload process")
        >>> try:
        ...     # Upload logic here
        ...     logger.log("Upload completed successfully")
        ... except Exception as e:
        ...     logger.error(f"Upload failed: {str(e)}")
    """

    @abstractmethod
    def log(self, message: str) -> None:
        """
        Log an informational message.
        
        Used for general application flow tracking and debugging.
        Messages should be timestamped and persisted to the log file.
        
        Args:
            message: The message to log. Can include any relevant details
                    about the current operation.
        
        Example:
            >>> logger.log("Processing video: video_123")
            >>> logger.log(f"Downloaded {bytes_downloaded} bytes")
        """
        ...

    @abstractmethod
    def error(self, message: str) -> None:
        """
        Log an error message.
        
        Used for recording errors that may require investigation.
        Should include stack traces when available.
        
        Args:
            message: The error message, typically including exception details
                    and context about what operation failed.
        
        Example:
            >>> try:
            ...     upload_video()
            ... except Exception as e:
            ...     logger.error(f"Failed to upload video_123: {e}")
        """
        ...

    @abstractmethod
    def warn(self, message: str) -> None:
        """
        Log a warning message.
        
        Used for non-critical issues that should be monitored but don't
        prevent operation completion.
        
        Args:
            message: The warning message describing the condition that
                    triggered the warning.
        
        Example:
            >>> if retry_count > 3:
            ...     logger.warn(f"High retry count ({retry_count}) for video_123")
            >>> if file_size > 1_000_000_000:  # 1GB
            ...     logger.warn("Large file size may cause slow upload")
        """
        ...


class IFileOperations(Protocol):
    """
    File system operations abstraction for dependency injection.
    
    This protocol enables testing by allowing mock implementations and provides
    a consistent interface for all file operations. Implementations should handle
    encoding (UTF-8 by default) and proper resource cleanup.
    
    Example:
        >>> file_ops: IFileOperations = FileOperations()
        >>> # Read configuration
        >>> config_data = file_ops.read_file("config.json")
        >>> # Save progress
        >>> file_ops.write_file("progress.json", json.dumps(progress))
        >>> # Append to log
        >>> file_ops.append_file("upload.log", f"{timestamp}: Upload complete\n")
    """

    @abstractmethod
    def read_file(self, path: Union[str, PathLike[str]]) -> str:
        """
        Read entire file contents as a string.
        
        Reads the file synchronously with UTF-8 encoding. For large files,
        consider using create_read_stream() instead.
        
        Args:
            path: Path to the file to read. Can be string or Path object.
        
        Returns:
            The complete file contents as a string.
        
        Raises:
            FileNotFoundError: If the file doesn't exist.
            PermissionError: If the file can't be read due to permissions.
            UnicodeDecodeError: If the file contains invalid UTF-8.
        
        Example:
            >>> # Read JSON configuration
            >>> json_str = file_ops.read_file("config.json")
            >>> config = json.loads(json_str)
            >>> 
            >>> # Read with Path object
            >>> from pathlib import Path
            >>> content = file_ops.read_file(Path.home() / ".config" / "app.conf")
        """
        ...

    @abstractmethod
    def write_file(self, path: Union[str, PathLike[str]], content: str) -> None:
        """
        Write string content to a file, replacing existing content.
        
        Creates parent directories if they don't exist. Uses UTF-8 encoding.
        For atomic writes, implementations should write to a temp file and rename.
        
        Args:
            path: Path where the file should be written.
            content: String content to write to the file.
        
        Raises:
            PermissionError: If the file can't be written due to permissions.
            OSError: If the disk is full or path is invalid.
        
        Example:
            >>> # Save JSON data
            >>> progress_data = {"processed": ["video1", "video2"]}
            >>> file_ops.write_file("progress.json", json.dumps(progress_data, indent=2))
            >>> 
            >>> # Save with Path object
            >>> file_ops.write_file(Path("logs") / "error.log", error_message)
        """
        ...

    @abstractmethod
    def append_file(self, path: Union[str, PathLike[str]], content: str) -> None:
        """
        Append string content to an existing file.
        
        Creates the file if it doesn't exist. Useful for log files where
        you want to preserve existing content.
        
        Args:
            path: Path to the file to append to.
            content: String content to append. Should typically end with newline.
        
        Raises:
            PermissionError: If the file can't be written due to permissions.
            OSError: If the disk is full or path is invalid.
        
        Example:
            >>> # Append to log file
            >>> timestamp = datetime.now().isoformat()
            >>> file_ops.append_file("upload.log", f"[{timestamp}] Upload started\n")
            >>> 
            >>> # Append multiple lines
            >>> log_entries = ["Error 1", "Error 2", "Error 3"]
            >>> file_ops.append_file("errors.log", "\n".join(log_entries) + "\n")
        """
        ...

    @abstractmethod
    def exists(self, path: Union[str, PathLike[str]]) -> bool:
        """Check if file/directory exists."""
        ...

    @abstractmethod
    def unlink(self, path: Union[str, PathLike[str]]) -> None:
        """Delete file."""
        ...

    @abstractmethod
    def mkdir(self, path: Union[str, PathLike[str]], exist_ok: bool = False) -> None:
        """Create directory."""
        ...

    @abstractmethod
    def create_read_stream(self, path: Union[str, PathLike[str]]) -> BufferedReader:
        """Create readable stream."""
        ...

    @abstractmethod
    def create_write_stream(self, path: Union[str, PathLike[str]]) -> BufferedWriter:
        """Create writable stream."""
        ...

    @abstractmethod
    def stat(self, path: Union[str, PathLike[str]]) -> stat_result:
        """Get file statistics."""
        ...


class IAuthenticationService(Protocol):
    """
    OAuth2 authentication service interface for Google APIs.
    
    Manages the complete OAuth2 flow including initial authorization, token
    persistence, and automatic token refresh. Implementations should follow
    Google's OAuth2 best practices for installed applications.
    
    The typical authentication flow:
    1. Check for saved tokens (load_saved_tokens)
    2. If no valid tokens, generate auth URL (get_auth_url)
    3. User authorizes and provides code
    4. Exchange code for tokens (get_tokens_from_code)
    5. Save tokens for future use (save_tokens)
    6. Use credentials for API calls (get_authenticated_client)
    
    Example:
        >>> auth_service: IAuthenticationService = AuthenticationService(config, file_ops, logger)
        >>> 
        >>> # Initialize authentication
        >>> credentials = auth_service.initialize()
        >>> 
        >>> # Use credentials with Google APIs
        >>> youtube = build('youtube', 'v3', credentials=credentials)
        >>> drive = build('drive', 'v3', credentials=credentials)
    """

    @abstractmethod
    def initialize(self) -> Credentials:
        """
        Sets up authentication and returns ready-to-use OAuth2 credentials.
        
        This is the main entry point that handles the complete auth flow:
        - Attempts to load saved tokens
        - Refreshes expired tokens automatically
        - Initiates new auth flow if needed
        - Saves tokens after successful auth
        
        Returns:
            Authenticated Google OAuth2 credentials ready for API use.
        
        Raises:
            AuthenticationError: If authentication fails after retries.
            FileNotFoundError: If credentials.json is missing.
        
        Example:
            >>> # First time - will open browser for auth
            >>> creds = auth_service.initialize()
            >>> print("Authentication successful!")
            >>> 
            >>> # Subsequent runs - uses saved tokens
            >>> creds = auth_service.initialize()  # No browser needed
        """
        ...

    @abstractmethod
    def get_auth_url(self) -> str:
        """
        Generates the OAuth2 consent URL for user authorization.
        
        Creates a URL that users visit to grant permissions. The URL includes
        the requested scopes and redirect URI configured in Google Cloud Console.
        
        Returns:
            The authorization URL that users should visit in their browser.
        
        Example:
            >>> url = auth_service.get_auth_url()
            >>> print(f"Please visit: {url}")
            >>> print("After authorizing, paste the code here:")
            >>> code = input().strip()
            >>> tokens = auth_service.get_tokens_from_code(code)
        """
        ...

    @abstractmethod
    def get_tokens_from_code(self, code: str) -> AuthTokens:
        """
        Exchanges an authorization code for access and refresh tokens.
        
        After the user authorizes and is redirected, they receive a code.
        This method exchanges that code for tokens that can be used to
        access Google APIs.
        
        Args:
            code: The authorization code from the OAuth2 callback.
                  Usually copied from the redirect URL parameter.
        
        Returns:
            OAuth2 tokens including access_token and refresh_token.
        
        Raises:
            InvalidGrantError: If the code is invalid or expired.
            NetworkError: If the token exchange request fails.
        
        Example:
            >>> # After user authorizes and gets code
            >>> code = "4/0AX4XfWgFj3..."
            >>> tokens = auth_service.get_tokens_from_code(code)
            >>> print(f"Access token: {tokens.access_token[:20]}...")
            >>> auth_service.save_tokens(tokens)
        """
        ...

    @abstractmethod
    def save_tokens(self, tokens: AuthTokens) -> None:
        """
        Persists OAuth2 tokens to storage for future use.
        
        Tokens should be stored securely. The refresh token is especially
        sensitive as it provides long-term access. Consider encryption
        for production use.
        
        Args:
            tokens: The OAuth2 tokens to save, including refresh_token.
        
        Raises:
            IOError: If tokens cannot be written to storage.
        
        Example:
            >>> tokens = auth_service.get_tokens_from_code(auth_code)
            >>> auth_service.save_tokens(tokens)
            >>> print("Tokens saved! Future runs won't need browser auth.")
        """
        ...

    @abstractmethod
    def load_saved_tokens(self) -> Optional[AuthTokens]:
        """
        Retrieves previously saved OAuth2 tokens from storage.
        
        Attempts to load tokens from the configured storage location.
        Returns None if no tokens are found or if they're corrupted.
        
        Returns:
            Saved OAuth2 tokens or None if not found/invalid.
        
        Example:
            >>> saved_tokens = auth_service.load_saved_tokens()
            >>> if saved_tokens:
            ...     print("Found saved authentication")
            ...     if saved_tokens.expiry_date < time.time() * 1000:
            ...         print("But tokens are expired, will refresh...")
            ... else:
            ...     print("No saved auth, need to authenticate")
        """
        ...

    @abstractmethod
    def get_authenticated_client(self) -> Credentials:
        """
        Returns the current authenticated OAuth2 credentials.
        
        This method should only be called after initialize(). It returns
        the credentials that can be used with Google API client libraries.
        
        Returns:
            The authenticated credentials for API access.
        
        Raises:
            RuntimeError: If called before initialize().
        
        Example:
            >>> # After initialization
            >>> creds = auth_service.get_authenticated_client()
            >>> 
            >>> # Use with any Google API
            >>> youtube_service = build('youtube', 'v3', credentials=creds)
            >>> sheets_service = build('sheets', 'v4', credentials=creds)
        """
        ...


class IGoogleDriveService(Protocol):
    """
    Google Drive API operations interface.
    
    Provides methods for downloading files from Google Drive, optimized for
    large video files. Implementations should handle authentication, retries,
    and efficient streaming downloads.
    
    Example:
        >>> drive_service: IGoogleDriveService = GoogleDriveService(
        ...     credentials, file_ops, logger
        ... )
        >>> 
        >>> # Download with progress tracking
        >>> def show_progress(current: int, total: int) -> None:
        ...     percent = (current / total) * 100
        ...     print(f"Downloaded: {percent:.1f}%")
        >>> 
        >>> drive_service.download_file(
        ...     "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        ...     "./videos/tutorial.mp4",
        ...     show_progress
        ... )
    """

    @abstractmethod
    def download_file(
        self,
        file_id: str,
        destination_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """
        Downloads a file from Google Drive to the local filesystem.
        
        Handles large files efficiently using chunked downloads. Automatically
        retries on network failures. Creates parent directories if needed.
        
        Args:
            file_id: Google Drive file ID. Can be extracted from share URLs:
                    - https://drive.google.com/file/d/{file_id}/view
                    - https://drive.google.com/open?id={file_id}
            destination_path: Local path where the file will be saved.
            progress_callback: Optional callback for download progress.
                             Called with (bytes_downloaded, total_bytes).
        
        Raises:
            FileNotFoundError: If the Drive file doesn't exist.
            PermissionError: If the file isn't accessible.
            IOError: If the download fails or disk is full.
        
        Example:
            >>> # Simple download
            >>> drive_service.download_file(
            ...     "1ABC123def456",
            ...     "/tmp/video.mp4"
            ... )
            >>> 
            >>> # Download with progress bar
            >>> from tqdm import tqdm
            >>> pbar = None
            >>> 
            >>> def update_progress(current: int, total: int) -> None:
            ...     nonlocal pbar
            ...     if pbar is None:
            ...         pbar = tqdm(total=total, unit='B', unit_scale=True)
            ...     pbar.update(current - pbar.n)
            >>> 
            >>> drive_service.download_file(file_id, output_path, update_progress)
            >>> pbar.close()
        """
        ...


class IGoogleSheetsService(Protocol):
    """
    Google Sheets API operations interface.
    
    Provides methods for reading video metadata from Google Sheets. Implementations
    should handle authentication, rate limiting, and data validation.
    
    Expected spreadsheet format:
    | A: Drive Link | B: Title | C: Description | D: Tags | E: Unique ID |
    |---------------|----------|----------------|---------|-------------|
    | https://...   | Video 1  | Description... | tag1,tag2 | video_001 |
    
    Example:
        >>> sheets_service: IGoogleSheetsService = GoogleSheetsService(credentials)
        >>> 
        >>> # Read video metadata
        >>> rows = sheets_service.fetch_spreadsheet_data(
        ...     "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
        ...     "Videos!A2:E100"
        ... )
        >>> 
        >>> print(f"Found {len(rows)} videos to process")
        >>> for row in rows[:5]:
        ...     print(f"- {row[1]}")  # Print titles
    """

    @abstractmethod
    def fetch_spreadsheet_data(self, spreadsheet_id: str, range: str) -> List[List[str]]:
        """
        Retrieves data from a specified Google Sheets range.
        
        Fetches all values in the specified range. Empty cells are returned
        as empty strings. The result is a 2D list matching the sheet structure.
        
        Args:
            spreadsheet_id: The ID of the Google Sheets document.
                           Found in the URL: /spreadsheets/d/{spreadsheet_id}/edit
            range: A1 notation range to fetch. Examples:
                   - "Sheet1!A:E" - All data in columns A through E
                   - "Videos!A2:E100" - Specific range, skipping header
                   - "Sheet1" - Entire sheet
        
        Returns:
            2D list where each inner list represents a row. Empty cells
            are empty strings. Rows are trimmed of trailing empty cells.
        
        Raises:
            PermissionError: If the spreadsheet isn't accessible.
            ValueError: If the spreadsheet ID or range is invalid.
            NetworkError: If the API request fails.
        
        Example:
            >>> # Read all video data
            >>> all_rows = sheets_service.fetch_spreadsheet_data(
            ...     "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            ...     "Sheet1!A:E"
            ... )
            >>> 
            >>> # Skip header row
            >>> video_rows = all_rows[1:] if all_rows else []
            >>> 
            >>> # Process each row
            >>> for row_num, row in enumerate(video_rows, start=2):
            ...     if len(row) >= 5:  # Ensure all columns present
            ...         drive_link, title, desc, tags, unique_id = row[:5]
            ...         print(f"Row {row_num}: {title} (ID: {unique_id})")
        """
        ...


class IProgressTracker(Protocol):
    """
    Upload progress tracking and resume capability interface.
    
    Enables resumable uploads by persisting progress to disk. Tracks successful
    uploads, failures, and current position in the spreadsheet. Essential for
    handling large batches and recovering from interruptions.
    
    Progress is saved after each video to minimize re-processing. Failed uploads
    are tracked separately to enable targeted retries.
    
    Example:
        >>> tracker: IProgressTracker = ProgressTracker(file_ops, "progress.json")
        >>> 
        >>> # Resume from previous session
        >>> progress = tracker.load_progress()
        >>> print(f"Resuming from row {progress.last_processed_row}")
        >>> print(f"Already processed: {len(progress.processed_ids)} videos")
        >>> 
        >>> # During processing
        >>> if not tracker.is_video_processed("video_123"):
        ...     try:
        ...         upload_video("video_123")
        ...         tracker.mark_video_processed("video_123")
        ...     except Exception as e:
        ...         tracker.mark_video_failed("video_123", str(e))
    """

    @abstractmethod
    def load_progress(self) -> UploadProgress:
        """
        Load saved progress from persistent storage.
        
        Reads the progress file and reconstructs the UploadProgress object.
        If no progress file exists, returns empty progress to start fresh.
        
        Returns:
            UploadProgress object with processed IDs, last row, and failures.
        
        Example:
            >>> progress = tracker.load_progress()
            >>> 
            >>> # Check what's been done
            >>> print(f"Processed videos: {len(progress.processed_ids)}")
            >>> print(f"Failed videos: {len(progress.failed_uploads)}")
            >>> print(f"Last row: {progress.last_processed_row}")
            >>> 
            >>> # Resume from last position
            >>> start_row = progress.last_processed_row + 1
        """
        ...

    @abstractmethod
    def save_progress(self, progress: UploadProgress) -> None:
        """
        Persist current progress to storage.
        
        Saves the complete progress state to disk. Should be called after
        each significant operation to enable resume on failure.
        
        Args:
            progress: The current progress state to save.
        
        Example:
            >>> # Manual save (usually done internally)
            >>> current_progress = tracker.get_progress()
            >>> current_progress.last_processed_row = 50
            >>> tracker.save_progress(current_progress)
        """
        ...

    @abstractmethod
    def mark_video_processed(self, unique_id: str) -> None:
        """
        Mark a video as successfully uploaded.
        
        Adds the video ID to the processed set and saves progress.
        Prevents duplicate uploads when resuming.
        
        Args:
            unique_id: The unique identifier of the processed video.
        
        Example:
            >>> # After successful upload
            >>> video_id = upload_to_youtube(video_data)
            >>> tracker.mark_video_processed(video_data.unique_id)
            >>> print(f"✓ Uploaded: {video_data.title}")
        """
        ...

    @abstractmethod
    def mark_video_failed(self, unique_id: str, error: str) -> None:
        """
        Record a failed upload attempt with error details.
        
        Tracks failures for debugging and retry operations. Each failure
        includes timestamp for age-based retry logic.
        
        Args:
            unique_id: The unique identifier of the failed video.
            error: Error message or exception details for debugging.
        
        Example:
            >>> try:
            ...     upload_video(video_data)
            ... except Exception as e:
            ...     tracker.mark_video_failed(
            ...         video_data.unique_id,
            ...         f"{type(e).__name__}: {str(e)}"
            ...     )
            ...     logger.error(f"Failed to upload {video_data.title}: {e}")
        """
        ...

    @abstractmethod
    def update_last_processed_row(self, row_number: int) -> None:
        """
        Update the last processed spreadsheet row number.
        
        Tracks position in the spreadsheet for efficient resuming.
        Row numbers are 1-indexed to match spreadsheet conventions.
        
        Args:
            row_number: The 1-indexed row number just processed.
        
        Example:
            >>> for row_num, video_data in enumerate(videos, start=2):
            ...     process_video(video_data)
            ...     tracker.update_last_processed_row(row_num)
            ...     # Progress saved automatically
        """
        ...

    @abstractmethod
    def is_video_processed(self, unique_id: str) -> bool:
        """
        Check if a video has already been successfully processed.
        
        Used to skip videos when resuming to avoid duplicate uploads.
        Only checks successful uploads, not failures.
        
        Args:
            unique_id: The unique identifier to check.
        
        Returns:
            True if the video was already uploaded successfully.
        
        Example:
            >>> # Skip already processed videos
            >>> for video in video_list:
            ...     if tracker.is_video_processed(video.unique_id):
            ...         logger.log(f"Skipping already uploaded: {video.title}")
            ...         continue
            ...     
            ...     # Process new video
            ...     upload_video(video)
        """
        ...

    @abstractmethod
    def get_progress(self) -> UploadProgress:
        """
        Get the current progress state.
        
        Returns the complete progress information including processed IDs,
        current position, and failure records.
        
        Returns:
            Current UploadProgress object.
        
        Example:
            >>> # Check progress mid-run
            >>> progress = tracker.get_progress()
            >>> 
            >>> # Generate summary
            >>> total_processed = len(progress.processed_ids)
            >>> total_failed = len(progress.failed_uploads)
            >>> success_rate = total_processed / (total_processed + total_failed) * 100
            >>> 
            >>> print(f"Progress: {total_processed} succeeded, {total_failed} failed")
            >>> print(f"Success rate: {success_rate:.1f}%")
        """
        ...


class IYouTubeService(Protocol):
    """
    YouTube API operations interface.
    
    Provides methods for uploading videos to YouTube with metadata. Implementations
    should handle authentication, chunked uploads for large files, and retry logic
    for network failures.
    
    YouTube has quotas and limits:
    - Daily upload quota varies by account
    - Maximum file size: 256GB or 12 hours
    - Title: max 100 characters
    - Description: max 5000 characters
    - Tags: max 500 characters total
    
    Example:
        >>> youtube_service: IYouTubeService = YouTubeService(credentials, file_ops)
        >>> 
        >>> # Prepare video data
        >>> video = VideoData(
        ...     driveLink="https://drive.google.com/...",
        ...     title="Python Tutorial - Episode 1",
        ...     description="Learn Python basics in this comprehensive tutorial...",
        ...     tags=["python", "tutorial", "programming", "beginners"],
        ...     uniqueId="tutorial_001"
        ... )
        >>> 
        >>> # Upload with progress
        >>> def show_progress(current: int, total: int) -> None:
        ...     percent = (current / total) * 100
        ...     print(f"Uploading: {percent:.1f}%")
        >>> 
        >>> video_id = youtube_service.upload_video(
        ...     "/tmp/tutorial.mp4",
        ...     video,
        ...     show_progress
        ... )
        >>> print(f"Uploaded! Watch at: https://youtube.com/watch?v={video_id}")
    """

    @abstractmethod
    def upload_video(
        self,
        video_path: str,
        video_data: VideoData,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> str:
        """
        Upload a video file to YouTube with metadata.
        
        Handles large files using resumable uploads. Automatically retries
        on network failures. Sets video as private by default for safety.
        
        Args:
            video_path: Local path to the video file to upload.
            video_data: Metadata for the video including title, description,
                       tags, and unique ID. The driveLink field is not used
                       for upload but included for reference.
            progress_callback: Optional callback for upload progress.
                              Called with (bytes_uploaded, total_bytes).
        
        Returns:
            The YouTube video ID of the uploaded video.
        
        Raises:
            FileNotFoundError: If the video file doesn't exist.
            ValueError: If video metadata exceeds YouTube limits.
            QuotaExceededError: If daily upload quota is exceeded.
            NetworkError: If upload fails after retries.
        
        Example:
            >>> # Simple upload
            >>> video_id = youtube_service.upload_video(
            ...     "./videos/tutorial.mp4",
            ...     video_data
            ... )
            >>> 
            >>> # Upload with detailed progress
            >>> from datetime import datetime
            >>> start_time = datetime.now()
            >>> 
            >>> def track_upload(current: int, total: int) -> None:
            ...     elapsed = (datetime.now() - start_time).seconds
            ...     if elapsed > 0:
            ...         speed = current / elapsed / 1_000_000  # MB/s
            ...         remaining = (total - current) / (current / elapsed)
            ...         print(f"Progress: {current}/{total} bytes "
            ...               f"({speed:.1f} MB/s, {remaining:.0f}s remaining)")
            >>> 
            >>> video_id = youtube_service.upload_video(
            ...     video_path, video_data, track_upload
            ... )
            >>> 
            >>> # Handle quota errors
            >>> try:
            ...     video_id = youtube_service.upload_video(path, data)
            ... except Exception as e:
            ...     if "quotaExceeded" in str(e):
            ...         print("Daily upload limit reached. Try again tomorrow.")
            ...     raise
        """
        ...


__all__ = [
    "ILogger",
    "IFileOperations",
    "IAuthenticationService",
    "IGoogleDriveService",
    "IGoogleSheetsService",
    "IProgressTracker",
    "IYouTubeService",
]
