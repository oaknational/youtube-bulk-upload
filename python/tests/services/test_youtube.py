"""Tests for YouTubeService."""

from unittest.mock import Mock, patch, MagicMock

import pytest
from google.oauth2.credentials import Credentials
from googleapiclient.http import MediaFileUpload

from interfaces import IFileOperations
from models import VideoData
from services.youtube import YouTubeService


class TestYouTubeService:
    """Test YouTubeService."""

    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials."""
        return Mock(spec=Credentials)

    @pytest.fixture
    def mock_file_ops(self):
        """Create mock file operations."""
        return Mock(spec=IFileOperations)

    @pytest.fixture
    def sample_video_data(self):
        """Create sample video data."""
        return VideoData(
            drive_link="https://drive.google.com/file/d/123/view",
            title="Test Video",
            description="Test Description",
            tags=["tag1", "tag2", "tag3"],
            unique_id="unique123"
        )

    @pytest.fixture
    def mock_youtube_service(self):
        """Create mock YouTube service."""
        mock_service = Mock()
        mock_videos = Mock()
        mock_service.videos.return_value = mock_videos
        return mock_service, mock_videos

    @pytest.fixture
    @patch("services.youtube.build")
    def youtube_service(
        self, mock_build, mock_credentials, mock_file_ops, mock_youtube_service
    ):
        """Create YouTubeService instance with mocked dependencies."""
        mock_service, _ = mock_youtube_service
        mock_build.return_value = mock_service
        return YouTubeService(mock_credentials, mock_file_ops)

    @patch("services.youtube.build")
    def test_initialization(self, mock_build, mock_credentials, mock_file_ops):
        """Test service initialization."""
        service = YouTubeService(mock_credentials, mock_file_ops)
        
        mock_build.assert_called_once_with("youtube", "v3", credentials=mock_credentials)
        assert service.service is not None
        assert service.file_operations == mock_file_ops

    @patch("services.youtube.MediaFileUpload")
    def test_upload_video_success(
        self, mock_media_class, youtube_service, mock_youtube_service, 
        mock_file_ops, sample_video_data
    ):
        """Test successful video upload."""
        _, mock_videos = mock_youtube_service
        
        # Mock file stats
        mock_stat = Mock()
        mock_stat.st_size = 1024 * 1024  # 1MB
        mock_file_ops.stat.return_value = mock_stat
        
        # Mock media upload
        mock_media = Mock()
        mock_media_class.return_value = mock_media
        
        # Mock insert request
        mock_request = Mock()
        mock_videos.insert.return_value = mock_request
        
        # Mock upload progress
        mock_request.next_chunk.side_effect = [
            (Mock(resumable_progress=512 * 1024), None),  # 50% done
            (None, {"id": "uploaded_video_123"}),  # Complete
        ]
        
        # Test upload
        progress_updates = []
        def track_progress(uploaded, total):
            progress_updates.append((uploaded, total))
        
        video_id = youtube_service.upload_video(
            "/tmp/video.mp4", sample_video_data, track_progress
        )
        
        # Verify result
        assert video_id == "uploaded_video_123"
        
        # Verify file stat call
        mock_file_ops.stat.assert_called_once_with("/tmp/video.mp4")
        
        # Verify media upload creation
        mock_media_class.assert_called_once_with(
            "/tmp/video.mp4",
            chunksize=-1,
            resumable=True,
            mimetype="video/*"
        )
        
        # Verify video insert call
        expected_body = {
            "snippet": {
                "title": "Test Video",
                "description": "Test Description",
                "tags": ["tag1", "tag2", "tag3"],
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "private",
                "selfDeclaredMadeForKids": False,
            },
        }
        mock_videos.insert.assert_called_once_with(
            part="snippet,status",
            body=expected_body,
            media_body=mock_media
        )
        
        # Verify progress updates
        assert progress_updates == [(512 * 1024, 1024 * 1024)]

    @patch("services.youtube.MediaFileUpload")
    def test_upload_video_without_progress_callback(
        self, mock_media_class, youtube_service, mock_youtube_service,
        mock_file_ops, sample_video_data
    ):
        """Test upload without progress callback."""
        _, mock_videos = mock_youtube_service
        
        # Mock file stats
        mock_stat = Mock()
        mock_stat.st_size = 1024
        mock_file_ops.stat.return_value = mock_stat
        
        # Mock successful upload
        mock_request = Mock()
        mock_videos.insert.return_value = mock_request
        mock_request.next_chunk.return_value = (None, {"id": "video123"})
        
        # Test upload without callback
        video_id = youtube_service.upload_video("/tmp/video.mp4", sample_video_data)
        
        assert video_id == "video123"

    @patch("services.youtube.MediaFileUpload")
    def test_upload_video_empty_response(
        self, mock_media_class, youtube_service, mock_youtube_service,
        mock_file_ops, sample_video_data
    ):
        """Test handling empty response from YouTube."""
        _, mock_videos = mock_youtube_service
        
        # Mock file stats
        mock_stat = Mock()
        mock_stat.st_size = 1024
        mock_file_ops.stat.return_value = mock_stat
        
        # Mock upload with empty response
        mock_request = Mock()
        mock_videos.insert.return_value = mock_request
        mock_request.next_chunk.return_value = (None, {})
        
        with pytest.raises(Exception, match="Upload succeeded but no video ID returned"):
            youtube_service.upload_video("/tmp/video.mp4", sample_video_data)

    @patch("services.youtube.MediaFileUpload")
    def test_upload_video_api_error(
        self, mock_media_class, youtube_service, mock_youtube_service,
        mock_file_ops, sample_video_data
    ):
        """Test handling API errors during upload."""
        _, mock_videos = mock_youtube_service
        
        # Mock file stats
        mock_stat = Mock()
        mock_stat.st_size = 1024
        mock_file_ops.stat.return_value = mock_stat
        
        # Mock API error
        mock_videos.insert.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="Failed to upload video: API Error"):
            youtube_service.upload_video("/tmp/video.mp4", sample_video_data)

    @patch("services.youtube.MediaFileUpload")
    def test_upload_video_file_not_found(
        self, mock_media_class, youtube_service, mock_file_ops, sample_video_data
    ):
        """Test handling file not found error."""
        # Mock file stat error
        mock_file_ops.stat.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(Exception, match="Failed to upload video: File not found"):
            youtube_service.upload_video("/tmp/nonexistent.mp4", sample_video_data)

    @patch("services.youtube.MediaFileUpload")
    def test_upload_large_video_multiple_chunks(
        self, mock_media_class, youtube_service, mock_youtube_service,
        mock_file_ops, sample_video_data
    ):
        """Test uploading large video with multiple chunks."""
        _, mock_videos = mock_youtube_service
        
        # Mock large file
        mock_stat = Mock()
        mock_stat.st_size = 100 * 1024 * 1024  # 100MB
        mock_file_ops.stat.return_value = mock_stat
        
        # Mock upload request
        mock_request = Mock()
        mock_videos.insert.return_value = mock_request
        
        # Simulate multiple chunks
        chunks = []
        for i in range(10):
            progress = (i + 1) * 10 * 1024 * 1024  # 10MB chunks
            status = Mock(resumable_progress=progress) if i < 9 else None
            response = None if i < 9 else {"id": "large_video_123"}
            chunks.append((status, response))
        
        mock_request.next_chunk.side_effect = chunks
        
        progress_updates = []
        def track_progress(uploaded, total):
            progress_updates.append((uploaded, total))
        
        video_id = youtube_service.upload_video(
            "/tmp/large_video.mp4", sample_video_data, track_progress
        )
        
        assert video_id == "large_video_123"
        assert len(progress_updates) == 9  # No callback on final chunk
        assert progress_updates[-1] == (90 * 1024 * 1024, 100 * 1024 * 1024)

    @patch("services.youtube.MediaFileUpload")
    def test_upload_video_with_special_characters(
        self, mock_media_class, youtube_service, mock_youtube_service,
        mock_file_ops
    ):
        """Test uploading video with special characters in metadata."""
        _, mock_videos = mock_youtube_service
        
        # Create video data with special characters
        special_video_data = VideoData(
            drive_link="https://drive.google.com/file/d/123/view",
            title="Test Video with émojis 🎥 and unicode ñ",
            description="Description with\nnewlines\tand tabs",
            tags=["tag-with-dash", "tag_with_underscore", "tagwithñ"],
            unique_id="unique123"
        )
        
        # Mock file stats
        mock_stat = Mock()
        mock_stat.st_size = 1024
        mock_file_ops.stat.return_value = mock_stat
        
        # Mock successful upload
        mock_request = Mock()
        mock_videos.insert.return_value = mock_request
        mock_request.next_chunk.return_value = (None, {"id": "special_video_123"})
        
        video_id = youtube_service.upload_video("/tmp/video.mp4", special_video_data)
        
        assert video_id == "special_video_123"
        
        # Verify special characters are preserved
        call_args = mock_videos.insert.call_args
        body = call_args[1]["body"]
        assert body["snippet"]["title"] == "Test Video with émojis 🎥 and unicode ñ"
        assert body["snippet"]["description"] == "Description with\nnewlines\tand tabs"

    @patch("services.youtube.MediaFileUpload")
    def test_upload_video_category_and_privacy(
        self, mock_media_class, youtube_service, mock_youtube_service, 
        mock_file_ops, sample_video_data
    ):
        """Test that video is uploaded with correct category and privacy settings."""
        _, mock_videos = mock_youtube_service
        
        # Mock file stats
        mock_stat = Mock()
        mock_stat.st_size = 1024
        mock_file_ops.stat.return_value = mock_stat
        
        # Mock media upload
        mock_media = Mock()
        mock_media_class.return_value = mock_media
        
        # Mock successful upload
        mock_request = Mock()
        mock_videos.insert.return_value = mock_request
        mock_request.next_chunk.return_value = (None, {"id": "video123"})
        
        youtube_service.upload_video("/tmp/video.mp4", sample_video_data)
        
        # Verify category and privacy settings
        call_args = mock_videos.insert.call_args
        body = call_args[1]["body"]
        assert body["snippet"]["categoryId"] == "22"  # People & Blogs
        assert body["status"]["privacyStatus"] == "private"
        assert body["status"]["selfDeclaredMadeForKids"] is False

    def test_implements_protocol(self, mock_credentials, mock_file_ops):
        """Test that YouTubeService implements IYouTubeService protocol."""
        from interfaces import IYouTubeService
        
        with patch("services.youtube.build"):
            service = YouTubeService(mock_credentials, mock_file_ops)
            # This would fail at runtime if protocol not satisfied
            _: IYouTubeService = service