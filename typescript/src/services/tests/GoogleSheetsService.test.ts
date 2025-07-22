import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { GoogleSheetsService } from '../GoogleSheetsService.js';
import type { OAuth2Client } from 'google-auth-library';

// Mock the Google Sheets API
const mockGet = vi.fn();
const mockSheets = {
  spreadsheets: {
    values: {
      get: mockGet
    }
  }
};

// Mock googleapis
vi.mock('googleapis', () => ({
  google: {
    sheets: vi.fn(() => mockSheets)
  }
}));

describe('GoogleSheetsService', () => {
  let sheetsService: GoogleSheetsService;
  let mockAuthClient: OAuth2Client;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Create mock auth client
    mockAuthClient = {} as OAuth2Client;

    // Create service instance
    sheetsService = new GoogleSheetsService(mockAuthClient);
  });

  describe('constructor', () => {
    it('should initialize Google Sheets API with auth client', async () => {
      const { google } = await import('googleapis');
      expect(google.sheets).toHaveBeenCalledWith({
        version: 'v4',
        auth: mockAuthClient
      });
    });
  });

  describe('fetchSpreadsheetData', () => {
    it('should fetch data from spreadsheet', async () => {
      const mockData = [
        ['Header1', 'Header2', 'Header3'],
        ['Row1Col1', 'Row1Col2', 'Row1Col3'],
        ['Row2Col1', 'Row2Col2', 'Row2Col3']
      ];

      mockGet.mockResolvedValue({
        data: {
          values: mockData
        }
      });

      const result = await sheetsService.fetchSpreadsheetData('test-spreadsheet-id', 'Sheet1!A:C');

      expect(mockGet).toHaveBeenCalledWith({
        spreadsheetId: 'test-spreadsheet-id',
        range: 'Sheet1!A:C'
      });
      expect(result).toEqual(mockData);
    });

    it('should return empty array when no data', async () => {
      mockGet.mockResolvedValue({
        data: {
          values: undefined
        }
      });

      const result = await sheetsService.fetchSpreadsheetData('test-spreadsheet-id', 'Sheet1!A:Z');

      expect(result).toEqual([]);
    });

    it('should return empty array when values is null', async () => {
      mockGet.mockResolvedValue({
        data: {
          values: null
        }
      });

      const result = await sheetsService.fetchSpreadsheetData('test-spreadsheet-id', 'Sheet1!A:Z');

      expect(result).toEqual([]);
    });

    it('should handle different range formats', async () => {
      const testCases = [
        { range: 'Sheet1', description: 'entire sheet' },
        { range: 'Sheet1!A1:E5', description: 'specific range' },
        { range: 'Sheet1!A:A', description: 'single column' },
        { range: 'Sheet1!1:1', description: 'single row' },
        { range: "'Sheet Name'!A:C", description: 'sheet name with spaces' }
      ];

      for (const testCase of testCases) {
        mockGet.mockResolvedValue({
          data: { values: [['test']] }
        });

        await sheetsService.fetchSpreadsheetData('spreadsheet-id', testCase.range);

        expect(mockGet).toHaveBeenCalledWith({
          spreadsheetId: 'spreadsheet-id',
          range: testCase.range
        });
      }
    });

    it('should handle large datasets', async () => {
      // Create a large dataset
      const largeData: string[][] = [];
      for (let i = 0; i < 1000; i++) {
        largeData.push([`Row${i}Col1`, `Row${i}Col2`, `Row${i}Col3`]);
      }

      mockGet.mockResolvedValue({
        data: { values: largeData }
      });

      const result = await sheetsService.fetchSpreadsheetData('test-spreadsheet-id', 'Sheet1');

      expect(result).toHaveLength(1000);
      expect(result[0]).toEqual(['Row0Col1', 'Row0Col2', 'Row0Col3']);
      expect(result[999]).toEqual(['Row999Col1', 'Row999Col2', 'Row999Col3']);
    });

    it('should throw on API error', async () => {
      mockGet.mockRejectedValue(new Error('API quota exceeded'));

      await expect(
        sheetsService.fetchSpreadsheetData('test-spreadsheet-id', 'Sheet1')
      ).rejects.toThrow('API quota exceeded');
    });

    it('should handle permission errors', async () => {
      const permissionError = new Error('The caller does not have permission');
      (permissionError as any).code = 403;
      mockGet.mockRejectedValue(permissionError);

      await expect(
        sheetsService.fetchSpreadsheetData('private-spreadsheet', 'Sheet1')
      ).rejects.toThrow('The caller does not have permission');
    });

    it('should handle not found errors', async () => {
      const notFoundError = new Error('Requested entity was not found');
      (notFoundError as any).code = 404;
      mockGet.mockRejectedValue(notFoundError);

      await expect(
        sheetsService.fetchSpreadsheetData('non-existent-id', 'Sheet1')
      ).rejects.toThrow('Requested entity was not found');
    });

    it('should handle empty response structure', async () => {
      mockGet.mockResolvedValue({
        data: {}
      });

      const result = await sheetsService.fetchSpreadsheetData('test-spreadsheet-id', 'Sheet1');

      expect(result).toEqual([]);
    });

    it('should handle cells with special characters', async () => {
      const specialData = [
        ['Normal', 'With\nNewline', 'With\tTab'],
        ['With"Quote', 'With\'Apostrophe', 'With,Comma'],
        ['🚀 Emoji', 'Unicode: ñáéíóú', 'Empty:']
      ];

      mockGet.mockResolvedValue({
        data: { values: specialData }
      });

      const result = await sheetsService.fetchSpreadsheetData('test-spreadsheet-id', 'Sheet1');

      expect(result).toEqual(specialData);
    });
  });
});