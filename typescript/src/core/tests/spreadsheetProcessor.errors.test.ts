import { describe, it, expect, vi, beforeEach } from 'vitest';
import { processVideoRows } from '../spreadsheetProcessor.js';
import {
  createMockLogger,
  createMockProgressTracker,
  createMockVideoProcessor,
  createTestRows,
  type MockLogger,
  type MockProgressTracker,
  type MockVideoProcessor,
} from './spreadsheetProcessor.helpers.js';

describe('processVideoRows - error handling', () => {
  let mockLogger: MockLogger;
  let mockProgressTracker: MockProgressTracker;
  let mockVideoProcessor: MockVideoProcessor;

  beforeEach(() => {
    vi.clearAllMocks();
    mockLogger = createMockLogger();
    mockProgressTracker = createMockProgressTracker();
    mockVideoProcessor = createMockVideoProcessor();
  });

  it('should skip empty rows', async () => {
    const [first, second] = createTestRows();
    const rows = [first, undefined as unknown as string[], second];

    mockProgressTracker.isVideoProcessed.mockReturnValue(false);
    mockVideoProcessor.processVideo.mockResolvedValue('youtube-id-123');

    await processVideoRows({
      rows,
      startRow: 0,
      logger: mockLogger,
      progressTracker: mockProgressTracker,
      videoProcessor: mockVideoProcessor,
    });

    expect(mockLogger.log).toHaveBeenCalledWith('Row 2 is empty, skipping');
    expect(mockVideoProcessor.processVideo).toHaveBeenCalledTimes(2);
  });

  it('should handle processing errors', async () => {
    const rows = [createTestRows()[0]];

    mockProgressTracker.isVideoProcessed.mockReturnValue(false);
    mockVideoProcessor.processVideo.mockRejectedValue(new Error('Upload failed'));

    await processVideoRows({
      rows,
      startRow: 0,
      logger: mockLogger,
      progressTracker: mockProgressTracker,
      videoProcessor: mockVideoProcessor,
    });

    expect(mockProgressTracker.markVideoFailed).toHaveBeenCalledWith('video1', 'Upload failed');
    expect(mockLogger.error).toHaveBeenCalledWith('Failed to process video1: Upload failed');
  });
});
