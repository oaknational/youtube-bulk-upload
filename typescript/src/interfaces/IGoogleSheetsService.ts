export interface IGoogleSheetsService {
  fetchSpreadsheetData(spreadsheetId: string, range: string): Promise<string[][]>;
}
