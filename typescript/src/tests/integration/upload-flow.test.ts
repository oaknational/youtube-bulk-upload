import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { YouTubeBulkUploader } from '../../core/YouTubeBulkUploader.js';
import { VideoProcessor } from '../../core/VideoProcessor.js';
import type { Config, VideoData } from '../../types/index.js';
import type { IAuthenticationService } from '../../interfaces/IAuthenticationService.js';
import type { IGoogleSheetsService } from '../../interfaces/IGoogleSheetsService.js';
import type { IProgressTracker } from '../../interfaces/IProgressTracker.js';
import type { ILogger } from '../../interfaces/ILogger.js';

describe('Upload Flow Integration Tests', () => {
  let uploader: YouTubeBulkUploader;
  let mockAuthService: IAuthenticationService;
  let mockSheetsService: IGoogleSheetsService;
  let mockVideoProcessor: VideoProcessor;
  let mockProgressTracker: IProgressTracker;
  let mockLogger: ILogger;

  const testConfig: Config = {
    clientId: 'test-client-id',
    clientSecret: 'test-client-secret',
    redirectUri: 'http://localhost:3000/callback',
    spreadsheetId: 'test-spreadsheet-id',
    sheetRange: 'Sheet1!A:E'
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Mock services
    mockAuthService = {
      initialize: vi.fn().mockResolvedValue({}),
      getAuthUrl: vi.fn(),
      getTokensFromCode: vi.fn(),
      saveTokens: vi.fn(),
      loadSavedTokens: vi.fn(),
      getAuthenticatedClient: vi.fn()
    };

    mockSheetsService = {
      fetchSpreadsheetData: vi.fn()
    };

    mockVideoProcessor = {
      processVideo: vi.fn()
    } as any;

    mockProgressTracker = {
      loadProgress: vi.fn().mockReturnValue({
        processedIds: new Set(),
        lastProcessedRow: 0,
        failedUploads: []
      }),
      saveProgress: vi.fn(),
      markVideoProcessed: vi.fn(),
      markVideoFailed: vi.fn(),
      updateLastProcessedRow: vi.fn(),
      isVideoProcessed: vi.fn().mockReturnValue(false),
      getProgress: vi.fn().mockReturnValue({
        processedIds: new Set(),
        lastProcessedRow: 0,
        failedUploads: []
      })
    };

    mockLogger = {
      log: vi.fn(),
      error: vi.fn(),
      warn: vi.fn()
    };

    // Create uploader
    uploader = new YouTubeBulkUploader(
      mockAuthService,
      mockSheetsService,
      mockVideoProcessor,
      mockProgressTracker,
      mockLogger,
      testConfig
    );
  });

  describe('Complete Upload Flow', () => {
    it('should process videos from spreadsheet successfully', async () => {
      const mockRows = [
        ['Drive Link', 'Title', 'Description', 'Tags', 'Unique ID'],
        ['https://drive.google.com/file/d/abc123', 'Video 1', 'Desc 1', 'tag1,tag2', 'vid1'],
        ['https://drive.google.com/file/d/def456', 'Video 2', 'Desc 2', 'tag3', 'vid2']
      ];

      (mockSheetsService.fetchSpreadsheetData as Mock).mockResolvedValue(mockRows);
      (mockVideoProcessor.processVideo as Mock).mockResolvedValue('youtube-id');

      // Initialize and process
      await uploader.initialize();
      await uploader.processSpreadsheet();

      // Verify flow
      expect(mockAuthService.initialize).toHaveBeenCalled();
      expect(mockSheetsService.fetchSpreadsheetData).toHaveBeenCalledWith(
        'test-spreadsheet-id',
        'Sheet1!A:E'
      );
      expect(mockVideoProcessor.processVideo).toHaveBeenCalledTimes(2);
      expect(mockProgressTracker.markVideoProcessed).toHaveBeenCalledTimes(2);
      expect(mockProgressTracker.updateLastProcessedRow).toHaveBeenCalledWith(2);
    });

    it('should skip already processed videos', async () => {
      const mockRows = [
        ['Drive Link', 'Title', 'Description', 'Tags', 'Unique ID'],
        ['https://drive.google.com/file/d/abc123', 'Video 1', 'Desc 1', 'tag1', 'vid1']
      ];

      (mockSheetsService.fetchSpreadsheetData as Mock).mockResolvedValue(mockRows);
      (mockProgressTracker.isVideoProcessed as Mock).mockReturnValue(true);

      await uploader.initialize();
      await uploader.processSpreadsheet();

      expect(mockVideoProcessor.processVideo).not.toHaveBeenCalled();
      expect(mockLogger.log).toHaveBeenCalledWith('Skipping already processed video: vid1');
    });

    it('should handle empty spreadsheet', async () => {
      (mockSheetsService.fetchSpreadsheetData as Mock).mockResolvedValue([]);

      await uploader.initialize();
      await uploader.processSpreadsheet();

      expect(mockVideoProcessor.processVideo).not.toHaveBeenCalled();
      expect(mockLogger.log).toHaveBeenCalledWith('No data found in spreadsheet');
    });

    it('should recover from individual video failures', async () => {
      const mockRows = [
        ['Drive Link', 'Title', 'Description', 'Tags', 'Unique ID'],
        ['https://drive.google.com/file/d/abc', 'Video 1', 'Desc 1', 'tag1', 'vid1'],
        ['https://drive.google.com/file/d/def', 'Video 2', 'Desc 2', 'tag2', 'vid2'],
        ['https://drive.google.com/file/d/ghi', 'Video 3', 'Desc 3', 'tag3', 'vid3']
      ];

      (mockSheetsService.fetchSpreadsheetData as Mock).mockResolvedValue(mockRows);
      (mockVideoProcessor.processVideo as Mock)
        .mockResolvedValueOnce('youtube-1')
        .mockRejectedValueOnce(new Error('Upload failed'))
        .mockResolvedValueOnce('youtube-3');

      await uploader.initialize();
      await uploader.processSpreadsheet();

      // All videos should be attempted
      expect(mockVideoProcessor.processVideo).toHaveBeenCalledTimes(3);
      
      // Two should succeed
      expect(mockProgressTracker.markVideoProcessed).toHaveBeenCalledWith('vid1');
      expect(mockProgressTracker.markVideoProcessed).toHaveBeenCalledWith('vid3');
      
      // One should fail
      expect(mockProgressTracker.markVideoFailed).toHaveBeenCalledWith('vid2', 'Upload failed');
      
      // Only successful videos update the last processed row
      expect(mockProgressTracker.updateLastProcessedRow).toHaveBeenCalledTimes(2);
      expect(mockProgressTracker.updateLastProcessedRow).toHaveBeenCalledWith(2);
      expect(mockProgressTracker.updateLastProcessedRow).toHaveBeenCalledWith(4);
    });
  });

  describe('Error Handling', () => {
    it('should handle authentication failure', async () => {
      (mockAuthService.initialize as Mock).mockRejectedValue(new Error('Auth failed'));

      await expect(uploader.initialize()).rejects.toThrow('Auth failed');
    });

    it('should handle spreadsheet API failure', async () => {
      (mockSheetsService.fetchSpreadsheetData as Mock).mockRejectedValue(
        new Error('API error')
      );

      await uploader.initialize();
      await expect(uploader.processSpreadsheet()).rejects.toThrow('API error');
    });
  });
});