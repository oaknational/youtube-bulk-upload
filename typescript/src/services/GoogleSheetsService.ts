import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import type { IGoogleSheetsService } from '../interfaces/IGoogleSheetsService.js';

export class GoogleSheetsService implements IGoogleSheetsService {
  private sheets;

  constructor(authClient: OAuth2Client) {
    this.sheets = google.sheets({ version: 'v4', auth: authClient });
  }

  async fetchSpreadsheetData(spreadsheetId: string, range: string): Promise<string[][]> {
    const response = await this.sheets.spreadsheets.values.get({
      spreadsheetId,
      range,
    });

    return response.data.values ?? [];
  }
}
