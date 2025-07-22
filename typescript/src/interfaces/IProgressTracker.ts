import type { UploadProgress } from '../types/index.js';

export interface IProgressTracker {
  loadProgress(): UploadProgress;
  saveProgress(progress: UploadProgress): void;
  markVideoProcessed(uniqueId: string): void;
  markVideoFailed(uniqueId: string, error: string): void;
  updateLastProcessedRow(row: number): void;
  isVideoProcessed(uniqueId: string): boolean;
  getProgress(): UploadProgress;
}
