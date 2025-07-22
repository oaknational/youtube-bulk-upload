import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { buildConfigFromEnv } from '../configBuilder.js';

describe('buildConfigFromEnv', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  describe('with all variables', () => {
    beforeEach(() => {
      process.env.CLIENT_ID = 'test-client-id';
      process.env.CLIENT_SECRET = 'test-client-secret';
      process.env.REDIRECT_URI = 'http://localhost:3000';
      process.env.SPREADSHEET_ID = 'test-spreadsheet-id';
    });

    it('should build config from environment', () => {
      const config = buildConfigFromEnv();

      expect(config.clientId).toBe('test-client-id');
      expect(config.clientSecret).toBe('test-client-secret');
      expect(config.redirectUri).toBe('http://localhost:3000');
      expect(config.spreadsheetId).toBe('test-spreadsheet-id');
    });

    it('should handle optional variables', () => {
      process.env.SHEET_RANGE = 'Sheet1!A:E';
      process.env.LOG_FILE = './custom-log.txt';

      const config = buildConfigFromEnv();

      expect(config.sheetRange).toBe('Sheet1!A:E');
      expect(config.logFile).toBe('./custom-log.txt');
    });
  });

  describe('missing variables', () => {
    it('should return empty strings', () => {
      const config = buildConfigFromEnv();

      expect(config.clientId).toBe('');
      expect(config.clientSecret).toBe('');
      expect(config.redirectUri).toBe('');
      expect(config.spreadsheetId).toBe('');
    });
  });
});
