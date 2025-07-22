import { describe, it, expect } from 'vitest';
import { validateRequiredConfigFields } from '../configValidator.js';
import type { Config } from '../../types/index.js';

const createValidConfig = (): Config => ({
  clientId: 'test-client-id',
  clientSecret: 'test-client-secret',
  redirectUri: 'http://localhost:3000',
  spreadsheetId: 'test-spreadsheet-id',
});

describe('validateRequiredConfigFields', () => {
  describe('valid config', () => {
    it('should return empty array when all required fields present', () => {
      const config = createValidConfig();
      const missingFields = validateRequiredConfigFields(config);
      expect(missingFields).toEqual([]);
    });

    it('should handle optional fields correctly', () => {
      const config = { ...createValidConfig(), sheetRange: undefined };
      const missingFields = validateRequiredConfigFields(config);
      expect(missingFields).toEqual([]);
    });
  });

  describe('missing fields', () => {
    it('should return missing clientId', () => {
      const config = { ...createValidConfig(), clientId: '' };
      const missingFields = validateRequiredConfigFields(config);
      expect(missingFields).toEqual(['clientId']);
    });

    it('should return multiple missing fields', () => {
      const config: Config = {
        clientId: '',
        clientSecret: '',
        redirectUri: 'http://localhost:3000',
        spreadsheetId: '',
      };
      const missingFields = validateRequiredConfigFields(config);
      expect(missingFields).toEqual(['clientId', 'clientSecret', 'spreadsheetId']);
    });
  });
});
