/**
 * Interface for Google Sheets API operations.
 * Provides methods for reading video metadata from Google Sheets spreadsheets
 * that contain information about videos to be uploaded to YouTube.
 */
export interface IGoogleSheetsService {
  /**
   * Fetches data from a Google Sheets spreadsheet within the specified range.
   * @param spreadsheetId - The unique identifier of the Google Sheets spreadsheet
   * @param range - The A1 notation range to fetch (e.g., "Sheet1!A1:E100" or "Sheet1")
   * @returns A 2D array of strings representing the spreadsheet data, where each inner array is a row
   * @throws May throw an error if the spreadsheet doesn't exist, access is denied, or the API call fails
   */
  fetchSpreadsheetData(spreadsheetId: string, range: string): Promise<string[][]>;
}
