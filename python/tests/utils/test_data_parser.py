"""Tests for data parser utility."""

import pytest

from models import VideoData
from utils.data_parser import parse_video_row


class TestParseVideoRow:
    """Test parse_video_row function."""

    def test_valid_row_with_all_fields(self) -> None:
        """Test parsing a valid row with all fields."""
        row = [
            "https://drive.google.com/file/d/123",
            "Test Video",
            "Test Description",
            "tag1, tag2, tag3",
            "unique123",
        ]

        result = parse_video_row(row)

        assert result is not None
        assert result.drive_link == "https://drive.google.com/file/d/123"
        assert result.title == "Test Video"
        assert result.description == "Test Description"
        assert result.tags == ["tag1", "tag2", "tag3"]
        assert result.unique_id == "unique123"

    def test_valid_row_with_empty_description(self) -> None:
        """Test parsing a row with empty description (allowed)."""
        row = ["https://drive.google.com/file/d/123", "Title", "", "tag1", "id123"]

        result = parse_video_row(row)

        assert result is not None
        assert result.description == ""

    def test_valid_row_with_empty_tags(self) -> None:
        """Test parsing a row with empty tags (allowed)."""
        row = ["https://drive.google.com/file/d/123", "Title", "Desc", "", "id123"]

        result = parse_video_row(row)

        assert result is not None
        assert result.tags == []

    def test_tags_with_extra_spaces(self) -> None:
        """Test that tags are properly trimmed."""
        row = [
            "https://drive.google.com/file/d/123",
            "Title",
            "Desc",
            "  tag1  ,   tag2   ,tag3  ",
            "id123",
        ]

        result = parse_video_row(row)

        assert result is not None
        assert result.tags == ["tag1", "tag2", "tag3"]

    def test_tags_with_empty_values(self) -> None:
        """Test that empty tag values are filtered out."""
        row = ["https://drive.google.com/file/d/123", "Title", "Desc", "tag1,,tag2,,,", "id123"]

        result = parse_video_row(row)

        assert result is not None
        assert result.tags == ["tag1", "tag2"]

    def test_row_with_extra_columns(self) -> None:
        """Test that extra columns are ignored."""
        row = [
            "https://drive.google.com/file/d/123",
            "Title",
            "Desc",
            "tag1",
            "id123",
            "extra",
            "columns",
        ]

        result = parse_video_row(row)

        assert result is not None
        assert result.unique_id == "id123"

    def test_row_with_whitespace(self) -> None:
        """Test that whitespace is trimmed from all fields."""
        row = [
            "  https://drive.google.com/file/d/123  ",
            "  Title  ",
            "  Description  ",
            "  tag1, tag2  ",
            "  id123  ",
        ]

        result = parse_video_row(row)

        assert result is not None
        assert result.drive_link == "https://drive.google.com/file/d/123"
        assert result.title == "Title"
        assert result.description == "Description"
        assert result.tags == ["tag1", "tag2"]
        assert result.unique_id == "id123"

    def test_row_too_short(self) -> None:
        """Test that rows with too few columns return None."""
        rows = [
            [],
            ["only one"],
            ["two", "columns"],
            ["three", "columns", "here"],
            ["four", "columns", "in", "row"],
        ]

        for row in rows:
            assert parse_video_row(row) is None

    def test_empty_drive_link(self) -> None:
        """Test that empty drive_link returns None."""
        row = ["", "Title", "Desc", "tags", "id123"]
        assert parse_video_row(row) is None

    def test_whitespace_only_drive_link(self) -> None:
        """Test that whitespace-only drive_link returns None."""
        row = ["   ", "Title", "Desc", "tags", "id123"]
        assert parse_video_row(row) is None

    def test_empty_title(self) -> None:
        """Test that empty title returns None."""
        row = ["https://drive.google.com/file/d/123", "", "Desc", "tags", "id123"]
        assert parse_video_row(row) is None

    def test_whitespace_only_title(self) -> None:
        """Test that whitespace-only title returns None."""
        row = ["https://drive.google.com/file/d/123", "   ", "Desc", "tags", "id123"]
        assert parse_video_row(row) is None

    def test_empty_unique_id(self) -> None:
        """Test that empty unique_id returns None."""
        row = ["https://drive.google.com/file/d/123", "Title", "Desc", "tags", ""]
        assert parse_video_row(row) is None

    def test_whitespace_only_unique_id(self) -> None:
        """Test that whitespace-only unique_id returns None."""
        row = ["https://drive.google.com/file/d/123", "Title", "Desc", "tags", "   "]
        assert parse_video_row(row) is None

    def test_all_required_fields_empty(self) -> None:
        """Test that all empty required fields returns None."""
        row = ["", "", "", "", ""]
        assert parse_video_row(row) is None
