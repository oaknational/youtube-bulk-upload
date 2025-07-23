"""Tests for Google Drive utilities."""

import pytest

from utils.drive_utils import extract_file_id_from_drive_link


class TestExtractFileIdFromDriveLink:
    """Test extract_file_id_from_drive_link function."""

    def test_standard_file_url(self) -> None:
        """Test extraction from standard file URL format."""
        links = [
            "https://drive.google.com/file/d/1abc123DEF456/view?usp=sharing",
            "https://drive.google.com/file/d/1abc123DEF456/view",
            "https://drive.google.com/file/d/1abc123DEF456",
            "drive.google.com/file/d/1abc123DEF456/edit",
        ]

        for link in links:
            assert extract_file_id_from_drive_link(link) == "1abc123DEF456"

    def test_query_parameter_format(self) -> None:
        """Test extraction from query parameter format."""
        links = [
            "https://drive.google.com/uc?id=1abc123DEF456",
            "https://drive.google.com/uc?export=download&id=1abc123DEF456",
            "drive.google.com/uc?id=1abc123DEF456&export=view",
        ]

        for link in links:
            assert extract_file_id_from_drive_link(link) == "1abc123DEF456"

    def test_open_link_format(self) -> None:
        """Test extraction from open link format."""
        links = [
            "https://drive.google.com/open?id=1abc123DEF456",
            "drive.google.com/open?id=1abc123DEF456&authuser=0",
        ]

        for link in links:
            assert extract_file_id_from_drive_link(link) == "1abc123DEF456"

    def test_file_id_with_underscores_and_hyphens(self) -> None:
        """Test extraction of file IDs containing underscores and hyphens."""
        links = [
            "https://drive.google.com/file/d/1abc_123-DEF_456/view",
            "https://drive.google.com/uc?id=1abc_123-DEF_456",
            "https://drive.google.com/open?id=1abc_123-DEF_456",
        ]

        for link in links:
            assert extract_file_id_from_drive_link(link) == "1abc_123-DEF_456"

    def test_complex_file_ids(self) -> None:
        """Test extraction of various real-world file ID formats."""
        test_cases = [
            ("https://drive.google.com/file/d/1A2B3C4D5E6F7G8H9I0J/view", "1A2B3C4D5E6F7G8H9I0J"),
            ("https://drive.google.com/uc?id=abc123ABC456_-xyz789", "abc123ABC456_-xyz789"),
            ("https://drive.google.com/open?id=_-_123abc_-_", "_-_123abc_-_"),
        ]

        for link, expected_id in test_cases:
            assert extract_file_id_from_drive_link(link) == expected_id

    def test_invalid_urls(self) -> None:
        """Test that invalid URLs return None."""
        invalid_links = [
            "",
            "not a url",
            "https://google.com",
            "https://drive.google.com",
            "https://drive.google.com/drive/folders/123",  # Folder, not file
            "https://docs.google.com/document/d/123/edit",  # Docs, not Drive
            "https://example.com/file/d/123/view",  # Wrong domain
        ]

        for link in invalid_links:
            assert extract_file_id_from_drive_link(link) is None

    def test_malformed_file_ids(self) -> None:
        """Test URLs with malformed or missing file IDs."""
        links = [
            "https://drive.google.com/file/d//view",  # Empty file ID
            "https://drive.google.com/uc?id=",  # Empty ID parameter
            "https://drive.google.com/open?id=",  # Empty ID parameter
        ]

        for link in links:
            assert extract_file_id_from_drive_link(link) is None

    def test_case_sensitivity(self) -> None:
        """Test that file IDs preserve case."""
        test_cases = [
            ("https://drive.google.com/file/d/AbCdEfGhIjKlMnOp/view", "AbCdEfGhIjKlMnOp"),
            ("https://drive.google.com/uc?id=UPPERCASE123", "UPPERCASE123"),
            ("https://drive.google.com/open?id=lowercase456", "lowercase456"),
        ]

        for link, expected_id in test_cases:
            assert extract_file_id_from_drive_link(link) == expected_id

    def test_url_with_fragments_and_extra_params(self) -> None:
        """Test URLs with fragments and extra parameters."""
        links = [
            "https://drive.google.com/file/d/1abc123DEF456/view?usp=sharing#heading=h.123",
            "https://drive.google.com/uc?export=download&id=1abc123DEF456&confirm=yes",
            "https://drive.google.com/open?id=1abc123DEF456&authuser=0&hl=en",
        ]

        for link in links:
            assert extract_file_id_from_drive_link(link) == "1abc123DEF456"
