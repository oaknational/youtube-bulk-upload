"""Tests for core type definitions."""

import json
from datetime import datetime

import pytest

from src.types import AuthTokens, Config, FailedUpload, UploadProgress, VideoData


class TestVideoData:
    """Test VideoData dataclass."""

    def test_valid_video_data(self) -> None:
        """Test creating valid VideoData."""
        video = VideoData(
            drive_link="https://drive.google.com/file/d/123",
            title="Test Video",
            description="Test Description",
            tags=["tag1", "tag2"],
            unique_id="unique123",
        )
        assert video.drive_link == "https://drive.google.com/file/d/123"
        assert video.title == "Test Video"
        assert video.description == "Test Description"
        assert video.tags == ["tag1", "tag2"]
        assert video.unique_id == "unique123"

    def test_empty_drive_link_raises_error(self) -> None:
        """Test that empty drive_link raises ValueError."""
        with pytest.raises(ValueError, match="drive_link cannot be empty"):
            VideoData(
                drive_link="",
                title="Test",
                description="Test",
                tags=[],
                unique_id="123",
            )

    def test_empty_title_raises_error(self) -> None:
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="title cannot be empty"):
            VideoData(
                drive_link="https://drive.google.com/file/d/123",
                title="",
                description="Test",
                tags=[],
                unique_id="123",
            )

    def test_empty_unique_id_raises_error(self) -> None:
        """Test that empty unique_id raises ValueError."""
        with pytest.raises(ValueError, match="unique_id cannot be empty"):
            VideoData(
                drive_link="https://drive.google.com/file/d/123",
                title="Test",
                description="Test",
                tags=[],
                unique_id="",
            )

    def test_empty_description_allowed(self) -> None:
        """Test that empty description is allowed."""
        video = VideoData(
            drive_link="https://drive.google.com/file/d/123",
            title="Test",
            description="",
            tags=[],
            unique_id="123",
        )
        assert video.description == ""

    def test_empty_tags_allowed(self) -> None:
        """Test that empty tags list is allowed."""
        video = VideoData(
            drive_link="https://drive.google.com/file/d/123",
            title="Test",
            description="Test",
            tags=[],
            unique_id="123",
        )
        assert video.tags == []


class TestFailedUpload:
    """Test FailedUpload dataclass."""

    def test_valid_failed_upload(self) -> None:
        """Test creating valid FailedUpload."""
        failed = FailedUpload(unique_id="123", error="Upload failed")
        assert failed.unique_id == "123"
        assert failed.error == "Upload failed"
        assert failed.timestamp  # Should have auto-generated timestamp

    def test_custom_timestamp(self) -> None:
        """Test creating FailedUpload with custom timestamp."""
        timestamp = "2023-01-01T00:00:00"
        failed = FailedUpload(unique_id="123", error="Error", timestamp=timestamp)
        assert failed.timestamp == timestamp

    def test_auto_generated_timestamp_format(self) -> None:
        """Test that auto-generated timestamp is valid ISO format."""
        failed = FailedUpload(unique_id="123", error="Error")
        # Should not raise exception
        datetime.fromisoformat(failed.timestamp.replace("Z", "+00:00"))

    def test_empty_unique_id_raises_error(self) -> None:
        """Test that empty unique_id raises ValueError."""
        with pytest.raises(ValueError, match="unique_id cannot be empty"):
            FailedUpload(unique_id="", error="Error")

    def test_empty_error_raises_error(self) -> None:
        """Test that empty error raises ValueError."""
        with pytest.raises(ValueError, match="error cannot be empty"):
            FailedUpload(unique_id="123", error="")


class TestUploadProgress:
    """Test UploadProgress dataclass."""

    def test_default_values(self) -> None:
        """Test UploadProgress with default values."""
        progress = UploadProgress()
        assert progress.processed_ids == set()
        assert progress.last_processed_row == 0
        assert progress.failed_uploads == []

    def test_with_values(self) -> None:
        """Test UploadProgress with provided values."""
        failed = FailedUpload(unique_id="123", error="Error")
        progress = UploadProgress(
            processed_ids={"id1", "id2"},
            last_processed_row=5,
            failed_uploads=[failed],
        )
        assert progress.processed_ids == {"id1", "id2"}
        assert progress.last_processed_row == 5
        assert len(progress.failed_uploads) == 1
        assert progress.failed_uploads[0] == failed

    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        failed = FailedUpload(unique_id="123", error="Error", timestamp="2023-01-01")
        progress = UploadProgress(
            processed_ids={"id1", "id2"},
            last_processed_row=5,
            failed_uploads=[failed],
        )
        result = progress.to_dict()

        assert set(result["processed_ids"]) == {"id1", "id2"}
        assert result["last_processed_row"] == 5
        assert len(result["failed_uploads"]) == 1
        assert result["failed_uploads"][0] == {
            "unique_id": "123",
            "error": "Error",
            "timestamp": "2023-01-01",
        }

    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "processed_ids": ["id1", "id2"],
            "last_processed_row": 5,
            "failed_uploads": [
                {"unique_id": "123", "error": "Error", "timestamp": "2023-01-01"}
            ],
        }
        progress = UploadProgress.from_dict(data)

        assert progress.processed_ids == {"id1", "id2"}
        assert progress.last_processed_row == 5
        assert len(progress.failed_uploads) == 1
        assert progress.failed_uploads[0].unique_id == "123"

    def test_from_dict_empty(self) -> None:
        """Test creation from empty dictionary."""
        progress = UploadProgress.from_dict({})
        assert progress.processed_ids == set()
        assert progress.last_processed_row == 0
        assert progress.failed_uploads == []

    def test_serialization_roundtrip(self) -> None:
        """Test that to_dict and from_dict are inverses."""
        original = UploadProgress(
            processed_ids={"id1", "id2", "id3"},
            last_processed_row=10,
            failed_uploads=[
                FailedUpload("f1", "Error 1", "2023-01-01"),
                FailedUpload("f2", "Error 2", "2023-01-02"),
            ],
        )

        # Serialize and deserialize
        serialized = json.dumps(original.to_dict())
        deserialized_data = json.loads(serialized)
        restored = UploadProgress.from_dict(deserialized_data)

        # Check equality
        assert restored.processed_ids == original.processed_ids
        assert restored.last_processed_row == original.last_processed_row
        assert len(restored.failed_uploads) == len(original.failed_uploads)
        for i in range(len(original.failed_uploads)):
            assert restored.failed_uploads[i].unique_id == original.failed_uploads[i].unique_id
            assert restored.failed_uploads[i].error == original.failed_uploads[i].error
            assert restored.failed_uploads[i].timestamp == original.failed_uploads[i].timestamp


class TestConfig:
    """Test Config dataclass."""

    def test_valid_config(self) -> None:
        """Test creating valid Config."""
        config = Config(
            client_id="client123",
            client_secret="secret456",
            redirect_uri="http://localhost:8080",
            spreadsheet_id="sheet789",
        )
        assert config.client_id == "client123"
        assert config.client_secret == "secret456"
        assert config.redirect_uri == "http://localhost:8080"
        assert config.spreadsheet_id == "sheet789"
        # Check defaults
        assert config.sheet_range == "A:E"
        assert config.progress_file == "progress.json"
        assert config.log_file == "upload.log"
        assert config.token_file == "token.json"
        assert config.temp_dir == "./temp"

    def test_custom_optional_values(self) -> None:
        """Test Config with custom optional values."""
        config = Config(
            client_id="client123",
            client_secret="secret456",
            redirect_uri="http://localhost:8080",
            spreadsheet_id="sheet789",
            sheet_range="Sheet1!A:F",
            progress_file="/tmp/progress.json",
            log_file="/var/log/upload.log",
            token_file="/home/user/.token.json",
            temp_dir="/tmp/videos",
        )
        assert config.sheet_range == "Sheet1!A:F"
        assert config.progress_file == "/tmp/progress.json"
        assert config.log_file == "/var/log/upload.log"
        assert config.token_file == "/home/user/.token.json"
        assert config.temp_dir == "/tmp/videos"

    def test_empty_client_id_raises_error(self) -> None:
        """Test that empty client_id raises ValueError."""
        with pytest.raises(ValueError, match="client_id cannot be empty"):
            Config(
                client_id="",
                client_secret="secret",
                redirect_uri="http://localhost",
                spreadsheet_id="sheet",
            )

    def test_empty_client_secret_raises_error(self) -> None:
        """Test that empty client_secret raises ValueError."""
        with pytest.raises(ValueError, match="client_secret cannot be empty"):
            Config(
                client_id="client",
                client_secret="",
                redirect_uri="http://localhost",
                spreadsheet_id="sheet",
            )

    def test_empty_redirect_uri_raises_error(self) -> None:
        """Test that empty redirect_uri raises ValueError."""
        with pytest.raises(ValueError, match="redirect_uri cannot be empty"):
            Config(
                client_id="client",
                client_secret="secret",
                redirect_uri="",
                spreadsheet_id="sheet",
            )

    def test_empty_spreadsheet_id_raises_error(self) -> None:
        """Test that empty spreadsheet_id raises ValueError."""
        with pytest.raises(ValueError, match="spreadsheet_id cannot be empty"):
            Config(
                client_id="client",
                client_secret="secret",
                redirect_uri="http://localhost",
                spreadsheet_id="",
            )


class TestAuthTokens:
    """Test AuthTokens dataclass."""

    def test_default_values(self) -> None:
        """Test AuthTokens with default values."""
        tokens = AuthTokens()
        assert tokens.access_token is None
        assert tokens.refresh_token is None
        assert tokens.scope is None
        assert tokens.token_type is None
        assert tokens.expiry_date is None

    def test_with_values(self) -> None:
        """Test AuthTokens with provided values."""
        tokens = AuthTokens(
            access_token="access123",
            refresh_token="refresh456",
            scope="https://www.googleapis.com/auth/drive.readonly",
            token_type="Bearer",
            expiry_date=1234567890,
        )
        assert tokens.access_token == "access123"
        assert tokens.refresh_token == "refresh456"
        assert tokens.scope == "https://www.googleapis.com/auth/drive.readonly"
        assert tokens.token_type == "Bearer"
        assert tokens.expiry_date == 1234567890

    def test_to_dict_all_values(self) -> None:
        """Test conversion to dictionary with all values."""
        tokens = AuthTokens(
            access_token="access123",
            refresh_token="refresh456",
            scope="scope",
            token_type="Bearer",
            expiry_date=1234567890,
        )
        result = tokens.to_dict()
        assert result == {
            "access_token": "access123",
            "refresh_token": "refresh456",
            "scope": "scope",
            "token_type": "Bearer",
            "expiry_date": 1234567890,
        }

    def test_to_dict_partial_values(self) -> None:
        """Test conversion to dictionary with partial values."""
        tokens = AuthTokens(access_token="access123", refresh_token="refresh456")
        result = tokens.to_dict()
        assert result == {
            "access_token": "access123",
            "refresh_token": "refresh456",
        }
        # None values should be excluded
        assert "scope" not in result
        assert "token_type" not in result
        assert "expiry_date" not in result

    def test_from_dict_all_values(self) -> None:
        """Test creation from dictionary with all values."""
        data = {
            "access_token": "access123",
            "refresh_token": "refresh456",
            "scope": "scope",
            "token_type": "Bearer",
            "expiry_date": 1234567890,
        }
        tokens = AuthTokens.from_dict(data)
        assert tokens.access_token == "access123"
        assert tokens.refresh_token == "refresh456"
        assert tokens.scope == "scope"
        assert tokens.token_type == "Bearer"
        assert tokens.expiry_date == 1234567890

    def test_from_dict_partial_values(self) -> None:
        """Test creation from dictionary with partial values."""
        data = {"access_token": "access123"}
        tokens = AuthTokens.from_dict(data)
        assert tokens.access_token == "access123"
        assert tokens.refresh_token is None
        assert tokens.scope is None
        assert tokens.token_type is None
        assert tokens.expiry_date is None

    def test_from_dict_empty(self) -> None:
        """Test creation from empty dictionary."""
        tokens = AuthTokens.from_dict({})
        assert tokens.access_token is None
        assert tokens.refresh_token is None
        assert tokens.scope is None
        assert tokens.token_type is None
        assert tokens.expiry_date is None

    def test_serialization_roundtrip(self) -> None:
        """Test that to_dict and from_dict are inverses."""
        original = AuthTokens(
            access_token="access",
            refresh_token="refresh",
            scope="scope1 scope2",
            token_type="Bearer",
            expiry_date=1234567890,
        )

        # Serialize and deserialize
        serialized = json.dumps(original.to_dict())
        deserialized_data = json.loads(serialized)
        restored = AuthTokens.from_dict(deserialized_data)

        # Check equality
        assert restored.access_token == original.access_token
        assert restored.refresh_token == original.refresh_token
        assert restored.scope == original.scope
        assert restored.token_type == original.token_type
        assert restored.expiry_date == original.expiry_date