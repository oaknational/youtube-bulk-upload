import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { GoogleDriveService } from '../GoogleDriveService.js';
import type { OAuth2Client } from 'google-auth-library';
import type { IFileOperations } from '../../interfaces/IFileOperations.js';
import type { ILogger } from '../../interfaces/ILogger.js';
import { EventEmitter } from 'events';
import type { Writable } from 'stream';

// Create mock stream
class MockStream extends EventEmitter {
  pipe(destination: any) {
    // Simulate successful download
    setTimeout(() => {
      this.emit('end');
    }, 0);
    return destination;
  }
}

// Mock the Google Drive API
const mockGet = vi.fn();
const mockDrive = {
  files: {
    get: mockGet
  }
};

// Mock googleapis
vi.mock('googleapis', () => ({
  google: {
    drive: vi.fn(() => mockDrive)
  }
}));

describe('GoogleDriveService', () => {
  let driveService: GoogleDriveService;
  let mockAuthClient: OAuth2Client;
  let mockFileOps: IFileOperations;
  let mockLogger: ILogger;
  let mockWriteStream: Writable;

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Create mock auth client
    mockAuthClient = {} as OAuth2Client;

    // Create mock write stream
    mockWriteStream = new EventEmitter() as any;

    // Setup file operations mock
    mockFileOps = {
      readFile: vi.fn(),
      writeFile: vi.fn(),
      appendFile: vi.fn(),
      exists: vi.fn(),
      unlink: vi.fn(),
      mkdir: vi.fn(),
      createReadStream: vi.fn(),
      createWriteStream: vi.fn().mockReturnValue(mockWriteStream),
      stat: vi.fn()
    };

    // Setup logger mock
    mockLogger = {
      log: vi.fn(),
      error: vi.fn(),
      warn: vi.fn()
    };

    // Create service instance
    driveService = new GoogleDriveService(mockAuthClient, mockFileOps, mockLogger);
  });

  describe('constructor', () => {
    it('should initialize Google Drive API with auth client', async () => {
      const { google } = await import('googleapis');
      expect(google.drive).toHaveBeenCalledWith({
        version: 'v3',
        auth: mockAuthClient
      });
    });
  });

  describe('downloadFile', () => {
    it('should download file successfully', async () => {
      const mockStream = new MockStream();
      mockGet.mockResolvedValue({
        data: mockStream
      });

      const downloadPromise = driveService.downloadFile('file-id-123', '/path/to/output.mp4');

      // Wait for the download to complete
      await downloadPromise;

      expect(mockGet).toHaveBeenCalledWith(
        { fileId: 'file-id-123', alt: 'media' },
        { responseType: 'stream' }
      );
      expect(mockFileOps.createWriteStream).toHaveBeenCalledWith('/path/to/output.mp4');
      expect(mockLogger.log).toHaveBeenCalledWith('Downloaded file: /path/to/output.mp4');
    });

    it('should handle download errors', async () => {
      const mockStream = new MockStream();
      const errorMessage = 'Network error';
      
      // Override pipe to trigger error
      mockStream.pipe = function(destination: any) {
        setTimeout(() => {
          this.emit('error', new Error(errorMessage));
        }, 0);
        return destination;
      };

      mockGet.mockResolvedValue({
        data: mockStream
      });

      await expect(
        driveService.downloadFile('file-id-456', '/path/to/output.mp4')
      ).rejects.toThrow(errorMessage);

      expect(mockLogger.error).toHaveBeenCalledWith(`Error downloading file: ${errorMessage}`);
    });

    it('should handle API errors', async () => {
      mockGet.mockRejectedValue(new Error('File not found'));

      await expect(
        driveService.downloadFile('non-existent-id', '/path/to/output.mp4')
      ).rejects.toThrow('File not found');

      expect(mockFileOps.createWriteStream).not.toHaveBeenCalled();
    });

    it('should handle permission errors', async () => {
      const permissionError = new Error('The user does not have sufficient permissions');
      (permissionError as any).code = 403;
      mockGet.mockRejectedValue(permissionError);

      await expect(
        driveService.downloadFile('private-file-id', '/path/to/output.mp4')
      ).rejects.toThrow('The user does not have sufficient permissions');
    });

    it('should handle quota exceeded errors', async () => {
      const quotaError = new Error('User rate limit exceeded');
      (quotaError as any).code = 429;
      mockGet.mockRejectedValue(quotaError);

      await expect(
        driveService.downloadFile('file-id', '/path/to/output.mp4')
      ).rejects.toThrow('User rate limit exceeded');
    });

    it('should download files with different paths', async () => {
      const testPaths = [
        '/absolute/path/video.mp4',
        './relative/path/video.mp4',
        '/path with spaces/video.mp4',
        '/path/with/特殊字符/video.mp4'
      ];

      for (const path of testPaths) {
        const mockStream = new MockStream();
        mockGet.mockResolvedValue({ data: mockStream });

        await driveService.downloadFile('file-id', path);

        expect(mockFileOps.createWriteStream).toHaveBeenCalledWith(path);
        expect(mockLogger.log).toHaveBeenCalledWith(`Downloaded file: ${path}`);
      }
    });

    it('should handle stream errors after pipe', async () => {
      const mockStream = new MockStream();
      
      // Override pipe to simulate error after piping starts
      mockStream.pipe = function(destination: any) {
        // Simulate some data transfer before error
        setTimeout(() => {
          this.emit('error', new Error('Stream interrupted'));
        }, 10);
        return destination;
      };

      mockGet.mockResolvedValue({ data: mockStream });

      await expect(
        driveService.downloadFile('file-id', '/path/to/output.mp4')
      ).rejects.toThrow('Stream interrupted');

      expect(mockLogger.error).toHaveBeenCalledWith('Error downloading file: Stream interrupted');
    });

    it('should handle large file downloads', async () => {
      const mockStream = new MockStream();
      
      // Simulate a longer download
      mockStream.pipe = function(destination: any) {
        let chunks = 0;
        const interval = setInterval(() => {
          chunks++;
          if (chunks >= 5) {
            clearInterval(interval);
            this.emit('end');
          }
        }, 10);
        return destination;
      };

      mockGet.mockResolvedValue({ data: mockStream });

      await driveService.downloadFile('large-file-id', '/path/to/large-file.mp4');

      expect(mockLogger.log).toHaveBeenCalledWith('Downloaded file: /path/to/large-file.mp4');
    });

    it('should handle concurrent downloads', async () => {
      const createMockStream = () => {
        const stream = new MockStream();
        stream.pipe = function(destination: any) {
          setTimeout(() => this.emit('end'), Math.random() * 50);
          return destination;
        };
        return stream;
      };

      mockGet.mockImplementation(() => 
        Promise.resolve({ data: createMockStream() })
      );

      // Start multiple downloads concurrently
      const downloads = [
        driveService.downloadFile('file-1', '/path/to/file1.mp4'),
        driveService.downloadFile('file-2', '/path/to/file2.mp4'),
        driveService.downloadFile('file-3', '/path/to/file3.mp4')
      ];

      // Wait for all to complete
      await Promise.all(downloads);

      expect(mockGet).toHaveBeenCalledTimes(3);
      expect(mockFileOps.createWriteStream).toHaveBeenCalledTimes(3);
      expect(mockLogger.log).toHaveBeenCalledTimes(3);
    });
  });
});