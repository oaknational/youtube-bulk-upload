import { vi } from 'vitest';
import type { ILogger } from '../../interfaces/ILogger.js';
import type { IProgressTracker } from '../../interfaces/IProgressTracker.js';
import type { VideoProcessor } from '../VideoProcessor.js';

export type MockLogger = {
  [K in keyof ILogger]: ReturnType<typeof vi.fn>;
};

export type MockProgressTracker = {
  [K in keyof IProgressTracker]: ReturnType<typeof vi.fn>;
};

export type MockVideoProcessor = {
  [K in keyof VideoProcessor]: ReturnType<typeof vi.fn>;
};

export const createMockLogger = (): MockLogger => ({
  log: vi.fn(),
  error: vi.fn(),
  warn: vi.fn(),
});

export const createMockProgressTracker = (): MockProgressTracker => ({
  isVideoProcessed: vi.fn(),
  markVideoProcessed: vi.fn(),
  markVideoFailed: vi.fn(),
  updateLastProcessedRow: vi.fn(),
  getProgress: vi.fn().mockReturnValue({
    processedIds: new Set(),
    lastProcessedRow: 0,
    failedUploads: [],
  }),
  loadProgress: vi.fn(),
  saveProgress: vi.fn(),
});

export const createMockVideoProcessor = (): MockVideoProcessor => ({
  processVideo: vi.fn(),
});

export const createTestRows = (): string[][] => [
  ['https://drive.google.com/file/d/123', 'Video 1', 'Description 1', 'tag1,tag2', 'video1'],
  ['https://drive.google.com/file/d/456', 'Video 2', 'Description 2', 'tag3,tag4', 'video2'],
];
