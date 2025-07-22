import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { buildConfigFromEnv } from '../configBuilder.js';

describe('buildConfigFromEnv - spreadsheet ID override', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('should allow override of spreadsheet ID', () => {
    process.env.SPREADSHEET_ID = 'env-spreadsheet-id';

    const config = buildConfigFromEnv('override-spreadsheet-id');

    expect(config.spreadsheetId).toBe('override-spreadsheet-id');
  });

  it('should use env var when no override provided', () => {
    process.env.SPREADSHEET_ID = 'env-spreadsheet-id';

    const config = buildConfigFromEnv();

    expect(config.spreadsheetId).toBe('env-spreadsheet-id');
  });
});
