import type { UploadProgress } from '../types/index.js';

/**
 * Interface for tracking upload progress and managing resume capabilities.
 * Provides methods to persist and retrieve upload progress, allowing the bulk upload
 * process to resume from where it left off in case of interruption.
 */
export interface IProgressTracker {
  /**
   * Loads the existing upload progress from persistent storage.
   * @returns The loaded UploadProgress object, or a new empty progress object if none exists
   * @throws May throw an error if the progress file is corrupted or cannot be read
   */
  loadProgress(): UploadProgress;

  /**
   * Saves the current upload progress to persistent storage.
   * @param progress - The UploadProgress object to save
   * @throws May throw an error if the progress cannot be written to storage
   */
  saveProgress(progress: UploadProgress): void;

  /**
   * Marks a video as successfully processed/uploaded.
   * @param uniqueId - The unique identifier of the processed video
   */
  markVideoProcessed(uniqueId: string): void;

  /**
   * Records a failed video upload attempt with error details.
   * @param uniqueId - The unique identifier of the failed video
   * @param error - The error message describing why the upload failed
   */
  markVideoFailed(uniqueId: string, error: string): void;

  /**
   * Updates the last processed row number in the spreadsheet.
   * @param row - The row number that was last processed
   */
  updateLastProcessedRow(row: number): void;

  /**
   * Checks if a video has already been processed.
   * @param uniqueId - The unique identifier of the video to check
   * @returns true if the video has been processed, false otherwise
   */
  isVideoProcessed(uniqueId: string): boolean;

  /**
   * Retrieves the current upload progress state.
   * @returns The current UploadProgress object
   */
  getProgress(): UploadProgress;
}
