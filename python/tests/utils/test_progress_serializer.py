"""Tests for progress serialization utilities."""

import json

import pytest

from models import FailedUpload, UploadProgress
from utils.progress_serializer import deserialize_progress, serialize_progress


class TestSerializeProgress:
    """Test serialize_progress function."""

    def test_empty_progress(self) -> None:
        """Test serializing empty progress."""
        progress = UploadProgress()
        result = serialize_progress(progress)

        # Parse back to verify structure
        data = json.loads(result)
        assert data == {
            "processed_ids": [],
            "last_processed_row": 0,
            "failed_uploads": [],
        }

    def test_progress_with_data(self) -> None:
        """Test serializing progress with data."""
        progress = UploadProgress(
            processed_ids={"id1", "id2", "id3"},
            last_processed_row=10,
            failed_uploads=[
                FailedUpload("fail1", "Error 1", "2023-01-01T00:00:00Z"),
                FailedUpload("fail2", "Error 2", "2023-01-02T00:00:00Z"),
            ],
        )

        result = serialize_progress(progress)
        data = json.loads(result)

        # Check structure
        assert set(data["processed_ids"]) == {"id1", "id2", "id3"}
        assert data["last_processed_row"] == 10
        assert len(data["failed_uploads"]) == 2
        assert data["failed_uploads"][0] == {
            "unique_id": "fail1",
            "error": "Error 1",
            "timestamp": "2023-01-01T00:00:00Z",
        }

    def test_pretty_printed_json(self) -> None:
        """Test that JSON is pretty-printed with 2-space indentation."""
        progress = UploadProgress(processed_ids={"id1"})
        result = serialize_progress(progress)

        # Check for indentation
        lines = result.split("\n")
        assert len(lines) > 1  # Should be multi-line
        assert lines[1].startswith("  ")  # 2-space indentation

    def test_unicode_in_progress(self) -> None:
        """Test serializing progress with unicode characters."""
        progress = UploadProgress(
            processed_ids={"видео_123", "視頻_456"},
            failed_uploads=[FailedUpload("id1", "Error: 错误消息", "2023-01-01T00:00:00Z")],
        )

        result = serialize_progress(progress)
        data = json.loads(result)

        assert "видео_123" in data["processed_ids"]
        assert "視頻_456" in data["processed_ids"]
        assert data["failed_uploads"][0]["error"] == "Error: 错误消息"


class TestDeserializeProgress:
    """Test deserialize_progress function."""

    def test_valid_json(self) -> None:
        """Test deserializing valid JSON."""
        json_data = json.dumps(
            {
                "processed_ids": ["id1", "id2", "id3"],
                "last_processed_row": 5,
                "failed_uploads": [
                    {
                        "unique_id": "fail1",
                        "error": "Upload failed",
                        "timestamp": "2023-01-01T00:00:00Z",
                    }
                ],
            }
        )

        result = deserialize_progress(json_data)

        assert result.processed_ids == {"id1", "id2", "id3"}
        assert result.last_processed_row == 5
        assert len(result.failed_uploads) == 1
        assert result.failed_uploads[0].unique_id == "fail1"
        assert result.failed_uploads[0].error == "Upload failed"

    def test_empty_json(self) -> None:
        """Test deserializing empty JSON object."""
        result = deserialize_progress("{}")

        assert result.processed_ids == set()
        assert result.last_processed_row == 0
        assert result.failed_uploads == []

    def test_partial_json(self) -> None:
        """Test deserializing JSON with missing fields."""
        # Only processed_ids
        result = deserialize_progress('{"processed_ids": ["id1"]}')
        assert result.processed_ids == {"id1"}
        assert result.last_processed_row == 0
        assert result.failed_uploads == []

        # Only last_processed_row
        result = deserialize_progress('{"last_processed_row": 10}')
        assert result.processed_ids == set()
        assert result.last_processed_row == 10
        assert result.failed_uploads == []

    def test_invalid_json(self) -> None:
        """Test deserializing invalid JSON returns empty progress."""
        invalid_inputs = [
            "",
            "not json",
            "{invalid json}",
            '{"unclosed": ',
            "null",
            "undefined",
            '{"processed_ids": "not_a_list"}',  # Wrong type
        ]

        for invalid in invalid_inputs:
            result = deserialize_progress(invalid)
            assert result.processed_ids == set()
            assert result.last_processed_row == 0
            assert result.failed_uploads == []

    def test_roundtrip_serialization(self) -> None:
        """Test that serialize and deserialize are inverses."""
        original = UploadProgress(
            processed_ids={"id1", "id2", "id3", "id4"},
            last_processed_row=25,
            failed_uploads=[
                FailedUpload("f1", "Error 1", "2023-01-01T00:00:00Z"),
                FailedUpload("f2", "Error 2", "2023-01-02T00:00:00Z"),
                FailedUpload("f3", "Error 3", "2023-01-03T00:00:00Z"),
            ],
        )

        # Serialize and deserialize
        serialized = serialize_progress(original)
        restored = deserialize_progress(serialized)

        # Check equality
        assert restored.processed_ids == original.processed_ids
        assert restored.last_processed_row == original.last_processed_row
        assert len(restored.failed_uploads) == len(original.failed_uploads)

        for i, failed in enumerate(original.failed_uploads):
            assert restored.failed_uploads[i].unique_id == failed.unique_id
            assert restored.failed_uploads[i].error == failed.error
            assert restored.failed_uploads[i].timestamp == failed.timestamp

    def test_numeric_strings_as_ids(self) -> None:
        """Test that numeric strings are preserved as strings."""
        json_data = '{"processed_ids": ["123", "456", "789"]}'
        result = deserialize_progress(json_data)

        assert result.processed_ids == {"123", "456", "789"}

    def test_duplicate_ids_in_list(self) -> None:
        """Test that duplicate IDs in the list are deduplicated in set."""
        json_data = '{"processed_ids": ["id1", "id2", "id1", "id3", "id2"]}'
        result = deserialize_progress(json_data)

        assert result.processed_ids == {"id1", "id2", "id3"}

    def test_null_values(self) -> None:
        """Test handling of null values in JSON."""
        json_data = json.dumps(
            {
                "processed_ids": None,
                "last_processed_row": None,
                "failed_uploads": None,
            }
        )

        # Should return empty progress (from_dict handles None values)
        result = deserialize_progress(json_data)
        assert result.processed_ids == set()
        assert result.last_processed_row == 0
        assert result.failed_uploads == []
