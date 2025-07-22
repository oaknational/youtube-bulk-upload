import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { Logger } from '../Logger.js';
import type { IFileOperations } from '../../interfaces/IFileOperations.js';
import * as logging from '../../utils/logging.js';

// Create mock consola instance
const mockConsola = {
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn()
};

// Mock the consola module
vi.mock('consola', () => ({
  createConsola: vi.fn(() => mockConsola)
}));

// Mock the logging utils
vi.mock('../../utils/logging.js');

describe('Logger', () => {
  let logger: Logger;
  let mockFileOps: IFileOperations;
  let mockCreateLogMessage: Mock;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Setup file operations mock
    mockFileOps = {
      readFile: vi.fn(),
      writeFile: vi.fn(),
      appendFile: vi.fn(),
      exists: vi.fn(),
      unlink: vi.fn(),
      mkdir: vi.fn(),
      createReadStream: vi.fn(),
      createWriteStream: vi.fn(),
      stat: vi.fn()
    };

    // Setup createLogMessage mock
    mockCreateLogMessage = logging.createLogMessage as Mock;
    mockCreateLogMessage.mockImplementation((msg: string) => `[TIMESTAMP] ${msg}\n`);

    // Create logger instance
    logger = new Logger('/path/to/log.txt', mockFileOps);
  });

  describe('constructor', () => {
    it('should initialize with correct log file path and file operations', async () => {
      expect(logger).toBeDefined();
      // Verify createConsola was called with correct options
      const { createConsola } = await import('consola');
      expect(createConsola).toHaveBeenCalledWith({
        formatOptions: {
          date: true,
          colors: true,
        },
      });
    });
  });

  describe('log', () => {
    it('should log to console and append to file', () => {
      const message = 'Test log message';
      const formattedMessage = '[TIMESTAMP] Test log message\n';

      logger.log(message);

      // Verify console logging
      expect(mockConsola.log).toHaveBeenCalledWith(message);
      expect(mockConsola.log).toHaveBeenCalledTimes(1);

      // Verify file logging
      expect(mockCreateLogMessage).toHaveBeenCalledWith(message);
      expect(mockFileOps.appendFile).toHaveBeenCalledWith('/path/to/log.txt', formattedMessage);
    });

    it('should handle multiple log calls', () => {
      const messages = ['First message', 'Second message', 'Third message'];

      messages.forEach(msg => logger.log(msg));

      expect(mockConsola.log).toHaveBeenCalledTimes(3);
      expect(mockFileOps.appendFile).toHaveBeenCalledTimes(3);
      
      messages.forEach((msg, index) => {
        expect(mockConsola.log).toHaveBeenNthCalledWith(index + 1, msg);
        expect(mockCreateLogMessage).toHaveBeenNthCalledWith(index + 1, msg);
      });
    });
  });

  describe('error', () => {
    it('should log error to console and append to file with ERROR prefix', () => {
      const message = 'Test error message';
      const formattedMessage = '[TIMESTAMP] ERROR: Test error message\n';

      logger.error(message);

      // Verify console error logging
      expect(mockConsola.error).toHaveBeenCalledWith(message);
      expect(mockConsola.error).toHaveBeenCalledTimes(1);

      // Verify file logging with ERROR prefix
      expect(mockCreateLogMessage).toHaveBeenCalledWith(`ERROR: ${message}`);
      expect(mockFileOps.appendFile).toHaveBeenCalledWith('/path/to/log.txt', formattedMessage);
    });

    it('should handle error with stack trace', () => {
      const errorMessage = 'Critical error occurred\nStack trace: at function...';
      
      logger.error(errorMessage);

      expect(mockConsola.error).toHaveBeenCalledWith(errorMessage);
      expect(mockCreateLogMessage).toHaveBeenCalledWith(`ERROR: ${errorMessage}`);
    });
  });

  describe('warn', () => {
    it('should log warning to console and append to file with WARN prefix', () => {
      const message = 'Test warning message';
      const formattedMessage = '[TIMESTAMP] WARN: Test warning message\n';

      logger.warn(message);

      // Verify console warning logging
      expect(mockConsola.warn).toHaveBeenCalledWith(message);
      expect(mockConsola.warn).toHaveBeenCalledTimes(1);

      // Verify file logging with WARN prefix
      expect(mockCreateLogMessage).toHaveBeenCalledWith(`WARN: ${message}`);
      expect(mockFileOps.appendFile).toHaveBeenCalledWith('/path/to/log.txt', formattedMessage);
    });
  });

  describe('file operations error handling', () => {
    it('should throw if file append fails for log', () => {
      (mockFileOps.appendFile as Mock).mockImplementation(() => {
        throw new Error('File write failed');
      });

      // Should throw since Logger doesn't catch file write errors
      expect(() => logger.log('Test message')).toThrow('File write failed');
      expect(mockConsola.log).toHaveBeenCalled();
    });

    it('should throw if file append fails for error', () => {
      (mockFileOps.appendFile as Mock).mockImplementation(() => {
        throw new Error('File write failed');
      });

      // Should throw since Logger doesn't catch file write errors
      expect(() => logger.error('Error message')).toThrow('File write failed');
      expect(mockConsola.error).toHaveBeenCalled();
    });

    it('should throw if file append fails for warn', () => {
      (mockFileOps.appendFile as Mock).mockImplementation(() => {
        throw new Error('File write failed');
      });

      // Should throw since Logger doesn't catch file write errors
      expect(() => logger.warn('Warning message')).toThrow('File write failed');
      expect(mockConsola.warn).toHaveBeenCalled();
    });
  });

  describe('edge cases', () => {
    it('should handle empty messages', () => {
      logger.log('');
      logger.error('');
      logger.warn('');

      expect(mockConsola.log).toHaveBeenCalledWith('');
      expect(mockConsola.error).toHaveBeenCalledWith('');
      expect(mockConsola.warn).toHaveBeenCalledWith('');
      expect(mockFileOps.appendFile).toHaveBeenCalledTimes(3);
    });

    it('should handle very long messages', () => {
      const longMessage = 'A'.repeat(10000);
      
      logger.log(longMessage);

      expect(mockConsola.log).toHaveBeenCalledWith(longMessage);
      expect(mockCreateLogMessage).toHaveBeenCalledWith(longMessage);
    });

    it('should handle special characters in messages', () => {
      const specialMessage = 'Test\nwith\ttabs\rand\u0000null';
      
      logger.log(specialMessage);

      expect(mockConsola.log).toHaveBeenCalledWith(specialMessage);
      expect(mockCreateLogMessage).toHaveBeenCalledWith(specialMessage);
    });
  });
});