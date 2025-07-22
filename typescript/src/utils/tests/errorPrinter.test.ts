import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { printMissingConfigError } from '../errorPrinter.js';

describe('printMissingConfigError', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should print error for single missing field', () => {
    printMissingConfigError(['clientId']);

    expect(consoleErrorSpy).toHaveBeenCalledWith('Missing required environment variable: CLIENTID');
    expect(consoleErrorSpy).toHaveBeenCalledWith('Please set the following environment variables:');
    expect(consoleErrorSpy).toHaveBeenCalledWith('- CLIENT_ID');
    expect(consoleErrorSpy).toHaveBeenCalledWith('- CLIENT_SECRET');
    expect(consoleErrorSpy).toHaveBeenCalledWith('- REDIRECT_URI');
    expect(consoleErrorSpy).toHaveBeenCalledWith('- SPREADSHEET_ID (or pass as first argument)');
  });

  it('should print error for multiple missing fields', () => {
    printMissingConfigError(['clientId', 'clientSecret']);

    // The function calls console.error 5 times regardless of how many fields are missing:
    // 1. Missing required environment variable: {FIRST_FIELD}
    // 2. Please set the following environment variables:
    // 3. - CLIENT_ID
    // 4. - CLIENT_SECRET
    // 5. - REDIRECT_URI
    // 6. - SPREADSHEET_ID (or pass as first argument)
    expect(consoleErrorSpy).toHaveBeenCalledWith('Missing required environment variable: CLIENTID');
    expect(consoleErrorSpy).toHaveBeenCalledWith('Please set the following environment variables:');
    expect(consoleErrorSpy).toHaveBeenCalledTimes(6);
  });

  it('should handle empty array gracefully', () => {
    printMissingConfigError([]);

    expect(consoleErrorSpy).not.toHaveBeenCalled();
  });
});
