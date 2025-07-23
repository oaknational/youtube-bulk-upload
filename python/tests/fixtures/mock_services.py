"""Mock service factories for tests"""

from unittest.mock import AsyncMock, MagicMock, Mock, mock_open


def create_mock_file_ops() -> Mock:
    """Create mock IFileOperations"""
    mock = Mock()
    mock.read_file = Mock(return_value="{}")
    mock.write_file = Mock(return_value=None)
    mock.append_file = Mock(return_value=None)
    mock.exists = Mock(return_value=True)
    mock.unlink = Mock(return_value=None)
    mock.mkdir = Mock(return_value=None)
    mock.create_read_stream = Mock(return_value=mock_open(read_data=b"test data")())
    mock.create_write_stream = Mock(return_value=mock_open()())
    mock.stat = Mock(return_value=Mock(st_size=1024))
    return mock


def create_mock_logger() -> Mock:
    """Create mock ILogger"""
    mock = Mock()
    mock.log = Mock()
    mock.error = Mock()
    mock.warn = Mock()
    return mock


def create_mock_progress_tracker() -> Mock:
    """Create mock IProgressTracker"""
    mock = Mock()
    mock.load_progress = Mock(
        return_value=Mock(processed_ids=set(), last_processed_row=0, failed_uploads=[])
    )
    mock.save_progress = Mock()
    mock.mark_video_processed = Mock()
    mock.mark_video_failed = Mock()
    mock.update_last_processed_row = Mock()
    mock.is_video_processed = Mock(return_value=False)
    mock.get_progress = Mock(
        return_value=Mock(processed_ids=set(), last_processed_row=0, failed_uploads=[])
    )
    return mock


def create_mock_auth_service() -> Mock:
    """Create mock IAuthenticationService"""
    mock = Mock()
    # Create a mock credentials object
    mock_creds = Mock()
    mock_creds.token = "test-token"
    mock_creds.refresh_token = "test-refresh-token"
    mock_creds.expiry = None
    mock_creds.valid = True

    # Set up async methods
    mock.initialize = AsyncMock(return_value=mock_creds)
    mock.get_auth_url = Mock(return_value="http://auth.url")
    mock.get_tokens_from_code = AsyncMock(
        return_value={"access_token": "test", "refresh_token": "test-refresh"}
    )
    mock.save_tokens = AsyncMock()
    mock.load_saved_tokens = AsyncMock(return_value=None)
    mock.get_authenticated_client = Mock(return_value=mock_creds)
    return mock


def create_mock_sheets_service() -> Mock:
    """Create mock IGoogleSheetsService"""
    mock = Mock()
    mock.fetch_spreadsheet_data = AsyncMock(
        return_value=[
            ["Drive Link", "Title", "Description", "Tags", "Unique ID"],
            [
                "https://drive.google.com/file/d/abc123/view",
                "Test Video",
                "Test Description",
                "tag1,tag2",
                "video-001",
            ],
        ]
    )
    return mock


def create_mock_drive_service() -> Mock:
    """Create mock IGoogleDriveService"""
    mock = Mock()
    mock.download_file = AsyncMock()
    return mock


def create_mock_youtube_service() -> Mock:
    """Create mock IYouTubeService"""
    mock = Mock()
    mock.upload_video = AsyncMock(return_value="youtube-video-id-123")
    return mock


def create_mock_google_api_service() -> Mock:
    """Create mock Google API service (for direct API mocking)"""
    mock = MagicMock()
    # Mock chain for sheets API
    mock.spreadsheets.return_value.values.return_value.get.return_value.execute.return_value = {
        "values": [
            ["Drive Link", "Title", "Description", "Tags", "Unique ID"],
            [
                "https://drive.google.com/file/d/abc123/view",
                "Test Video",
                "Test Description",
                "tag1,tag2",
                "video-001",
            ],
        ]
    }

    # Mock chain for drive API
    mock.files.return_value.get_media.return_value = Mock()

    # Mock chain for youtube API
    mock_request = Mock()
    mock_request.next_chunk.return_value = (Mock(progress=lambda: 1.0), {"id": "yt-123"})
    mock.videos.return_value.insert.return_value = mock_request

    return mock


def create_mock_credentials() -> Mock:
    """Create mock Google credentials"""
    mock = Mock()
    mock.token = "test-access-token"
    mock.refresh_token = "test-refresh-token"
    mock.token_uri = "https://oauth2.googleapis.com/token"
    mock.client_id = "test-client-id"
    mock.client_secret = "test-client-secret"
    mock.scopes = ["test-scope"]
    mock.expiry = None
    mock.valid = True
    mock.expired = False
    mock.refresh = Mock()
    return mock
