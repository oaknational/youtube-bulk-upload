import type { IProgressTracker } from '../interfaces/IProgressTracker.js';
import type { IFileOperations } from '../interfaces/IFileOperations.js';
import type { UploadProgress } from '../types/index.js';
import { serializeProgress, deserializeProgress } from '../utils/progressSerializer.js';

export class ProgressTracker implements IProgressTracker {
  private progress: UploadProgress;

  constructor(
    private readonly progressFile: string,
    private readonly fileOps: IFileOperations
  ) {
    this.progress = this.loadProgress();
  }

  loadProgress(): UploadProgress {
    const content = this.fileOps.readFile(this.progressFile);
    if (!content) {
      return {
        processedIds: new Set(),
        lastProcessedRow: 0,
        failedUploads: [],
      };
    }
    return deserializeProgress(content);
  }

  saveProgress(progress: UploadProgress): void {
    this.progress = progress;
    this.fileOps.writeFile(this.progressFile, serializeProgress(progress));
  }

  markVideoProcessed(uniqueId: string): void {
    this.progress.processedIds.add(uniqueId);
    this.saveProgress(this.progress);
  }

  markVideoFailed(uniqueId: string, error: string): void {
    this.progress.failedUploads.push({
      uniqueId,
      error,
      timestamp: new Date().toISOString(),
    });
    this.saveProgress(this.progress);
  }

  updateLastProcessedRow(row: number): void {
    this.progress.lastProcessedRow = row;
    this.saveProgress(this.progress);
  }

  isVideoProcessed(uniqueId: string): boolean {
    return this.progress.processedIds.has(uniqueId);
  }

  getProgress(): UploadProgress {
    return this.progress;
  }
}
