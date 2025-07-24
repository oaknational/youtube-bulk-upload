import * as path from 'path';
import type { IGoogleDriveService } from '../interfaces/IGoogleDriveService.js';
import type { IYouTubeService } from '../interfaces/IYouTubeService.js';
import type { IFileOperations } from '../interfaces/IFileOperations.js';
import type { VideoData, Config } from '../types/index.js';
import { extractFileIdFromDriveLink } from '../utils/driveUtils.js';

/**
 * Orchestrates the process of downloading videos from Google Drive and uploading them to YouTube.
 * 
 * This is the core business logic class that coordinates between the Drive and YouTube services.
 * It handles the complete workflow for a single video:
 * 1. Validates the Drive link and extracts file ID
 * 2. Downloads the video to a temporary location
 * 3. Uploads the video to YouTube with metadata
 * 4. Cleans up temporary files (even on failure)
 * 
 * @example
 * ```typescript
 * // Create processor with dependencies
 * const processor = new VideoProcessor(
 *   driveService,
 *   youtubeService,
 *   fileOps,
 *   config
 * );
 * 
 * // Process a single video
 * const videoData: VideoData = {
 *   driveLink: "https://drive.google.com/file/d/1abc123/view",
 *   title: "My Tutorial",
 *   description: "Learn something new...",
 *   tags: ["tutorial", "education"],
 *   uniqueId: "tutorial_001"
 * };
 * 
 * try {
 *   const youtubeId = await processor.processVideo(videoData);
 *   console.log(`Success! YouTube URL: https://youtube.com/watch?v=${youtubeId}`);
 * } catch (error) {
 *   console.error(`Failed to process ${videoData.uniqueId}:`, error);
 * }
 * ```
 */
export class VideoProcessor {
  /**
   * Creates a new VideoProcessor instance with injected dependencies.
   * 
   * @param driveService - Service for downloading files from Google Drive
   * @param youtubeService - Service for uploading videos to YouTube
   * @param fileOps - File system operations (for testing/mocking)
   * @param config - Application configuration including temp directory path
   */
  constructor(
    private readonly driveService: IGoogleDriveService,
    private readonly youtubeService: IYouTubeService,
    private readonly fileOps: IFileOperations,
    private readonly config: Config
  ) {}

  /**
   * Processes a single video: downloads from Drive and uploads to YouTube.
   * 
   * This method orchestrates the complete video processing workflow:
   * - Validates the Google Drive link format
   * - Creates a temporary directory if needed
   * - Downloads the video file from Google Drive
   * - Uploads the video to YouTube with metadata
   * - Cleans up the temporary file after upload (or on error)
   * 
   * The method provides console output for progress tracking during upload.
   * Temporary files are always cleaned up, even if the upload fails.
   * 
   * @param videoData - The metadata for the video to process, including:
   *   - driveLink: Google Drive URL of the video
   *   - title: YouTube video title
   *   - description: YouTube video description
   *   - tags: Array of tags for YouTube
   *   - uniqueId: Unique identifier for tracking
   * 
   * @returns Promise resolving to the YouTube video ID of the uploaded video
   * 
   * @throws {Error} When:
   *   - The Drive link is invalid or doesn't contain a file ID
   *   - The Drive file doesn't exist or isn't accessible
   *   - The YouTube upload fails (quota, network, etc.)
   *   - File system operations fail (disk full, permissions)
   * 
   * @example
   * ```typescript
   * // Basic usage
   * const youtubeId = await processor.processVideo(videoData);
   * 
   * // With error handling
   * try {
   *   const youtubeId = await processor.processVideo(videoData);
   *   progressTracker.markVideoProcessed(videoData.uniqueId);
   * } catch (error) {
   *   if (error.message.includes('quota')) {
   *     console.log('YouTube quota exceeded, stopping batch');
   *     throw error; // Re-throw to stop processing
   *   }
   *   // Log error but continue with next video
   *   progressTracker.markVideoFailed(videoData.uniqueId, error.message);
   * }
   * 
   * // Integration with progress tracking
   * for (const video of videos) {
   *   if (progressTracker.isVideoProcessed(video.uniqueId)) {
   *     console.log(`Skipping already processed: ${video.title}`);
   *     continue;
   *   }
   *   
   *   await processor.processVideo(video);
   * }
   * ```
   */
  async processVideo(videoData: VideoData): Promise<string> {
    // Extract file ID from various Google Drive URL formats
    // Supports: /file/d/{id}/view, /open?id={id}, /uc?id={id}
    const fileId = extractFileIdFromDriveLink(videoData.driveLink);
    if (!fileId) {
      throw new Error('Invalid Google Drive link');
    }

    // Ensure temp directory exists for storing downloaded videos
    // Default to './temp_videos' if not configured
    const tempDir = this.config.tempDir ?? './temp_videos';
    this.fileOps.mkdir(tempDir);

    // Create unique filename using video's unique ID to avoid conflicts
    // when processing multiple videos concurrently
    const tempVideoPath = path.join(tempDir, `${videoData.uniqueId}.mp4`);

    // Download video from Google Drive to temporary location
    // This may take a while for large files
    await this.driveService.downloadFile(fileId, tempVideoPath);

    try {
      // Upload to YouTube with metadata and progress tracking
      // Progress callback updates console with upload percentage
      const youtubeId = await this.youtubeService.uploadVideo(
        tempVideoPath,
        videoData,
        (progress) => {
          // Use carriage return to update same line for cleaner output
          process.stdout.write(`\rUploading ${videoData.uniqueId}: ${progress.toFixed(2)}%`);
        }
      );

      // New line after progress to prevent next log from overwriting
      process.stdout.write('\n');
      return youtubeId;
    } finally {
      // Always clean up temp file, even if upload fails
      // This prevents disk space issues when processing many videos
      this.fileOps.unlink(tempVideoPath);
    }
  }
}
