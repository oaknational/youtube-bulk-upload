import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { ProgressTracker } from '../ProgressTracker.js';
import type { IFileOperations } from '../../interfaces/IFileOperations.js';
import type { UploadProgress, FailedUpload } from '../../types/index.js';
import * as progressSerializer from '../../utils/progressSerializer.js';

// Mock the progress serializer utils
vi.mock('../../utils/progressSerializer.js');

describe('ProgressTracker', () => {
  let tracker: ProgressTracker;
  let mockFileOps: IFileOperations;
  let mockSerializeProgress: Mock;
  let mockDeserializeProgress: Mock;
  const progressFile = '/path/to/progress.json';

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

    // Setup serializer mocks
    mockSerializeProgress = progressSerializer.serializeProgress as Mock;
    mockDeserializeProgress = progressSerializer.deserializeProgress as Mock;

    // Default mock implementations
    mockSerializeProgress.mockImplementation((progress: UploadProgress) => 
      JSON.stringify({
        processedIds: Array.from(progress.processedIds),
        lastProcessedRow: progress.lastProcessedRow,
        failedUploads: progress.failedUploads
      })
    );

    mockDeserializeProgress.mockImplementation((content: string) => {
      const parsed = JSON.parse(content);
      return {
        processedIds: new Set(parsed.processedIds),
        lastProcessedRow: parsed.lastProcessedRow,
        failedUploads: parsed.failedUploads
      };
    });
  });

  describe('constructor and loadProgress', () => {
    it('should create new progress when file does not exist', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);

      tracker = new ProgressTracker(progressFile, mockFileOps);
      const progress = tracker.getProgress();

      expect(mockFileOps.readFile).toHaveBeenCalledWith(progressFile);
      expect(progress.processedIds.size).toBe(0);
      expect(progress.lastProcessedRow).toBe(0);
      expect(progress.failedUploads).toEqual([]);
    });

    it('should load existing progress from file', () => {
      const existingProgress: UploadProgress = {
        processedIds: new Set(['video1', 'video2']),
        lastProcessedRow: 5,
        failedUploads: [{
          uniqueId: 'video3',
          error: 'Upload failed',
          timestamp: '2023-01-01T00:00:00.000Z'
        }]
      };

      const serialized = JSON.stringify({
        processedIds: Array.from(existingProgress.processedIds),
        lastProcessedRow: existingProgress.lastProcessedRow,
        failedUploads: existingProgress.failedUploads
      });

      (mockFileOps.readFile as Mock).mockReturnValue(serialized);
      mockDeserializeProgress.mockReturnValue(existingProgress);

      tracker = new ProgressTracker(progressFile, mockFileOps);
      const progress = tracker.getProgress();

      expect(mockFileOps.readFile).toHaveBeenCalledWith(progressFile);
      expect(mockDeserializeProgress).toHaveBeenCalledWith(serialized);
      expect(progress).toEqual(existingProgress);
    });
  });

  describe('saveProgress', () => {
    it('should save progress to file', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      const newProgress: UploadProgress = {
        processedIds: new Set(['video1', 'video2']),
        lastProcessedRow: 3,
        failedUploads: []
      };

      const expectedSerialized = 'serialized-progress';
      mockSerializeProgress.mockReturnValue(expectedSerialized);

      tracker.saveProgress(newProgress);

      expect(mockSerializeProgress).toHaveBeenCalledWith(newProgress);
      expect(mockFileOps.writeFile).toHaveBeenCalledWith(progressFile, expectedSerialized);
      expect(tracker.getProgress()).toEqual(newProgress);
    });
  });

  describe('markVideoProcessed', () => {
    it('should add video ID to processed set and save', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      tracker.markVideoProcessed('video1');

      const progress = tracker.getProgress();
      expect(progress.processedIds.has('video1')).toBe(true);
      expect(mockFileOps.writeFile).toHaveBeenCalled();
    });

    it('should handle multiple videos', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      tracker.markVideoProcessed('video1');
      tracker.markVideoProcessed('video2');
      tracker.markVideoProcessed('video3');

      const progress = tracker.getProgress();
      expect(progress.processedIds.size).toBe(3);
      expect(progress.processedIds.has('video1')).toBe(true);
      expect(progress.processedIds.has('video2')).toBe(true);
      expect(progress.processedIds.has('video3')).toBe(true);
      expect(mockFileOps.writeFile).toHaveBeenCalledTimes(3);
    });

    it('should handle duplicate video IDs', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      tracker.markVideoProcessed('video1');
      tracker.markVideoProcessed('video1'); // Duplicate

      const progress = tracker.getProgress();
      expect(progress.processedIds.size).toBe(1);
      expect(mockFileOps.writeFile).toHaveBeenCalledTimes(2);
    });
  });

  describe('markVideoFailed', () => {
    it('should add failed upload with error and timestamp', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      const mockDate = '2023-12-01T12:00:00.000Z';
      vi.spyOn(Date.prototype, 'toISOString').mockReturnValue(mockDate);

      tracker.markVideoFailed('video1', 'Network error');

      const progress = tracker.getProgress();
      expect(progress.failedUploads).toHaveLength(1);
      expect(progress.failedUploads[0]).toEqual({
        uniqueId: 'video1',
        error: 'Network error',
        timestamp: mockDate
      });
      expect(mockFileOps.writeFile).toHaveBeenCalled();
    });

    it('should handle multiple failed uploads', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      tracker.markVideoFailed('video1', 'Error 1');
      tracker.markVideoFailed('video2', 'Error 2');
      tracker.markVideoFailed('video1', 'Error 3'); // Same video can fail multiple times

      const progress = tracker.getProgress();
      expect(progress.failedUploads).toHaveLength(3);
      expect(mockFileOps.writeFile).toHaveBeenCalledTimes(3);
    });
  });

  describe('updateLastProcessedRow', () => {
    it('should update last processed row and save', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      tracker.updateLastProcessedRow(10);

      const progress = tracker.getProgress();
      expect(progress.lastProcessedRow).toBe(10);
      expect(mockFileOps.writeFile).toHaveBeenCalled();
    });

    it('should handle row number updates', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      tracker.updateLastProcessedRow(5);
      tracker.updateLastProcessedRow(10);
      tracker.updateLastProcessedRow(7); // Can go backwards

      const progress = tracker.getProgress();
      expect(progress.lastProcessedRow).toBe(7);
      expect(mockFileOps.writeFile).toHaveBeenCalledTimes(3);
    });
  });

  describe('isVideoProcessed', () => {
    it('should return true for processed videos', () => {
      const existingProgress: UploadProgress = {
        processedIds: new Set(['video1', 'video2']),
        lastProcessedRow: 0,
        failedUploads: []
      };

      (mockFileOps.readFile as Mock).mockReturnValue('serialized');
      mockDeserializeProgress.mockReturnValue(existingProgress);

      tracker = new ProgressTracker(progressFile, mockFileOps);

      expect(tracker.isVideoProcessed('video1')).toBe(true);
      expect(tracker.isVideoProcessed('video2')).toBe(true);
    });

    it('should return false for unprocessed videos', () => {
      const existingProgress: UploadProgress = {
        processedIds: new Set(['video1', 'video2']),
        lastProcessedRow: 0,
        failedUploads: []
      };

      (mockFileOps.readFile as Mock).mockReturnValue('serialized');
      mockDeserializeProgress.mockReturnValue(existingProgress);

      tracker = new ProgressTracker(progressFile, mockFileOps);

      expect(tracker.isVideoProcessed('video3')).toBe(false);
      expect(tracker.isVideoProcessed('video4')).toBe(false);
    });
  });

  describe('getProgress', () => {
    it('should return current progress state', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      // Modify progress
      tracker.markVideoProcessed('video1');
      tracker.updateLastProcessedRow(5);
      tracker.markVideoFailed('video2', 'Error');

      const progress = tracker.getProgress();
      expect(progress.processedIds.has('video1')).toBe(true);
      expect(progress.lastProcessedRow).toBe(5);
      expect(progress.failedUploads).toHaveLength(1);
    });
  });

  describe('edge cases', () => {
    it('should handle empty string video IDs', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      tracker.markVideoProcessed('');
      expect(tracker.isVideoProcessed('')).toBe(true);
    });

    it('should handle very long error messages', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      const longError = 'E'.repeat(10000);
      tracker.markVideoFailed('video1', longError);

      const progress = tracker.getProgress();
      expect(progress.failedUploads[0].error).toBe(longError);
    });

    it('should handle file write errors gracefully', () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      tracker = new ProgressTracker(progressFile, mockFileOps);

      (mockFileOps.writeFile as Mock).mockImplementation(() => {
        throw new Error('Disk full');
      });

      // Should throw when trying to save
      expect(() => tracker.markVideoProcessed('video1')).toThrow('Disk full');
    });
  });
});