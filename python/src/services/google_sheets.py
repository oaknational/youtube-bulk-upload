"""Google Sheets service implementation."""

from typing import List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from interfaces import IGoogleSheetsService


class GoogleSheetsService(IGoogleSheetsService):
    """Google Sheets API operations implementation."""

    def __init__(self, credentials: Credentials) -> None:
        """
        Initialize Google Sheets service.

        Args:
            credentials: Authenticated Google credentials
        """
        self.service = build("sheets", "v4", credentials=credentials)

    def fetch_spreadsheet_data(self, spreadsheet_id: str, range: str) -> List[List[str]]:
        """
        Retrieves data from specified spreadsheet range.

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            range: A1 notation range (e.g., "Sheet1!A:E")

        Returns:
            List of rows, where each row is a list of cell values

        Raises:
            Exception: If API call fails
        """
        try:
            result = (
                self.service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=range)
                .execute()
            )
            
            values = result.get("values", [])
            
            # Ensure all values are strings
            return [[str(cell) if cell is not None else "" for cell in row] for row in values]
            
        except Exception as e:
            raise Exception(f"Failed to fetch spreadsheet data: {str(e)}") from e