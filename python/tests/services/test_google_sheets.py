"""Tests for GoogleSheetsService."""

from unittest.mock import Mock, patch

import pytest
from google.oauth2.credentials import Credentials

from services.google_sheets import GoogleSheetsService


class TestGoogleSheetsService:
    """Test GoogleSheetsService."""

    @pytest.fixture
    def mock_credentials(self):
        """Create mock credentials."""
        return Mock(spec=Credentials)

    @pytest.fixture
    def mock_sheets_service(self):
        """Create mock sheets service."""
        mock_service = Mock()
        mock_values = Mock()
        mock_service.spreadsheets.return_value.values.return_value = mock_values
        return mock_service, mock_values

    @pytest.fixture
    @patch("services.google_sheets.build")
    def sheets_service(self, mock_build, mock_credentials, mock_sheets_service):
        """Create GoogleSheetsService instance with mocked dependencies."""
        mock_service, _ = mock_sheets_service
        mock_build.return_value = mock_service
        return GoogleSheetsService(mock_credentials)

    @patch("services.google_sheets.build")
    def test_initialization(self, mock_build, mock_credentials):
        """Test service initialization."""
        service = GoogleSheetsService(mock_credentials)
        
        mock_build.assert_called_once_with("sheets", "v4", credentials=mock_credentials)
        assert service.service is not None

    def test_fetch_spreadsheet_data_success(self, sheets_service, mock_sheets_service):
        """Test successful spreadsheet data fetch."""
        _, mock_values = mock_sheets_service
        
        # Mock API response
        mock_values.get.return_value.execute.return_value = {
            "values": [
                ["Header1", "Header2", "Header3"],
                ["Row1Col1", "Row1Col2", "Row1Col3"],
                ["Row2Col1", "Row2Col2", "Row2Col3"],
            ]
        }
        
        result = sheets_service.fetch_spreadsheet_data("test_spreadsheet_id", "Sheet1!A:C")
        
        assert len(result) == 3
        assert result[0] == ["Header1", "Header2", "Header3"]
        assert result[1] == ["Row1Col1", "Row1Col2", "Row1Col3"]
        assert result[2] == ["Row2Col1", "Row2Col2", "Row2Col3"]
        
        mock_values.get.assert_called_once_with(
            spreadsheetId="test_spreadsheet_id",
            range="Sheet1!A:C"
        )

    def test_fetch_spreadsheet_data_empty(self, sheets_service, mock_sheets_service):
        """Test fetching empty spreadsheet."""
        _, mock_values = mock_sheets_service
        
        # Mock empty response
        mock_values.get.return_value.execute.return_value = {}
        
        result = sheets_service.fetch_spreadsheet_data("test_id", "Sheet1")
        
        assert result == []

    def test_fetch_spreadsheet_data_with_none_values(self, sheets_service, mock_sheets_service):
        """Test handling None values in cells."""
        _, mock_values = mock_sheets_service
        
        # Mock response with None values
        mock_values.get.return_value.execute.return_value = {
            "values": [
                ["Value1", None, "Value3"],
                [None, "Value2", None],
            ]
        }
        
        result = sheets_service.fetch_spreadsheet_data("test_id", "A1:C2")
        
        assert result == [
            ["Value1", "", "Value3"],
            ["", "Value2", ""],
        ]

    def test_fetch_spreadsheet_data_with_numbers(self, sheets_service, mock_sheets_service):
        """Test converting numeric values to strings."""
        _, mock_values = mock_sheets_service
        
        # Mock response with various types
        mock_values.get.return_value.execute.return_value = {
            "values": [
                ["Text", 123, 45.67],
                [True, False, None],
            ]
        }
        
        result = sheets_service.fetch_spreadsheet_data("test_id", "A1:C2")
        
        assert result == [
            ["Text", "123", "45.67"],
            ["True", "False", ""],
        ]

    def test_fetch_spreadsheet_data_api_error(self, sheets_service, mock_sheets_service):
        """Test handling API errors."""
        _, mock_values = mock_sheets_service
        
        # Mock API error
        mock_values.get.return_value.execute.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="Failed to fetch spreadsheet data: API Error"):
            sheets_service.fetch_spreadsheet_data("test_id", "Sheet1")

    def test_fetch_spreadsheet_data_permission_error(self, sheets_service, mock_sheets_service):
        """Test handling permission errors."""
        _, mock_values = mock_sheets_service
        
        # Mock permission error
        mock_values.get.return_value.execute.side_effect = PermissionError("Access denied")
        
        with pytest.raises(Exception, match="Failed to fetch spreadsheet data"):
            sheets_service.fetch_spreadsheet_data("test_id", "Sheet1")

    def test_different_range_formats(self, sheets_service, mock_sheets_service):
        """Test various A1 notation range formats."""
        _, mock_values = mock_sheets_service
        
        # Mock response
        mock_values.get.return_value.execute.return_value = {
            "values": [["Data"]]
        }
        
        # Test different range formats
        ranges = [
            "Sheet1",
            "Sheet1!A:Z",
            "Sheet1!A1:Z100",
            "'Sheet Name'!A:B",
            "A1:B2",
        ]
        
        for range_str in ranges:
            result = sheets_service.fetch_spreadsheet_data("test_id", range_str)
            assert result == [["Data"]]

    def test_large_spreadsheet(self, sheets_service, mock_sheets_service):
        """Test handling large spreadsheet data."""
        _, mock_values = mock_sheets_service
        
        # Mock large dataset
        large_data = [[f"Cell{i}_{j}" for j in range(100)] for i in range(1000)]
        mock_values.get.return_value.execute.return_value = {
            "values": large_data
        }
        
        result = sheets_service.fetch_spreadsheet_data("test_id", "Sheet1")
        
        assert len(result) == 1000
        assert len(result[0]) == 100
        assert result[0][0] == "Cell0_0"
        assert result[999][99] == "Cell999_99"

    def test_implements_protocol(self, mock_credentials):
        """Test that GoogleSheetsService implements IGoogleSheetsService protocol."""
        from interfaces import IGoogleSheetsService
        
        with patch("services.google_sheets.build"):
            service = GoogleSheetsService(mock_credentials)
            # This would fail at runtime if protocol not satisfied
            _: IGoogleSheetsService = service