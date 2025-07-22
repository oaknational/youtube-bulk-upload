import type { Config } from '../types/index.js';

export function buildConfigFromEnv(overrideSpreadsheetId?: string): Config {
  const config: Config = {
    clientId: process.env['CLIENT_ID'] ?? '',
    clientSecret: process.env['CLIENT_SECRET'] ?? '',
    redirectUri: process.env['REDIRECT_URI'] ?? '',
    spreadsheetId: overrideSpreadsheetId ?? process.env['SPREADSHEET_ID'] ?? '',
    sheetRange: process.env['SHEET_RANGE'],
    progressFile: process.env['PROGRESS_FILE'],
    logFile: process.env['LOG_FILE'],
    tokenFile: process.env['TOKEN_FILE'],
    tempDir: process.env['TEMP_DIR'],
  };

  return config;
}
