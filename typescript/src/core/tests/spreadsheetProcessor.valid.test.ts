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

describe('processVideoRows - valid processing', () => {
  let mockLogger: MockLogger;
  let mockProgressTracker: MockProgressTracker;
  let mockVideoProcessor: MockVideoProcessor;

  beforeEach(() => {
    vi.clearAllMocks();
    mockLogger = createMockLogger();
    mockProgressTracker = createMockProgressTracker();
    mockVideoProcessor = createMockVideoProcessor();
  });

  it('should process valid video rows', async () => {
    const rows = createTestRows();

    mockProgressTracker.isVideoProcessed.mockReturnValue(false);
    mockVideoProcessor.processVideo.mockResolvedValue('youtube-id-123');

    await processVideoRows({
      rows,
      startRow: 0,
      logger: mockLogger,
      progressTracker: mockProgressTracker,
      videoProcessor: mockVideoProcessor,
    });

    expect(mockVideoProcessor.processVideo).toHaveBeenCalledTimes(2);
    expect(mockProgressTracker.markVideoProcessed).toHaveBeenCalledTimes(2);
    expect(mockProgressTracker.updateLastProcessedRow).toHaveBeenCalledWith(1);
    expect(mockProgressTracker.updateLastProcessedRow).toHaveBeenCalledWith(2);
  });

  it('should skip already processed videos', async () => {
    const rows = [createTestRows()[0]];

    mockProgressTracker.isVideoProcessed.mockReturnValue(true);

    await processVideoRows({
      rows,
      startRow: 0,
      logger: mockLogger,
      progressTracker: mockProgressTracker,
      videoProcessor: mockVideoProcessor,
    });

    expect(mockVideoProcessor.processVideo).not.toHaveBeenCalled();
    expect(mockLogger.log).toHaveBeenCalledWith('Skipping already processed video: video1');
  });
});
