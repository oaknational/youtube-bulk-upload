import * as path from 'path';
import type { IGoogleDriveService } from '../interfaces/IGoogleDriveService.js';
import type { IYouTubeService } from '../interfaces/IYouTubeService.js';
import type { IFileOperations } from '../interfaces/IFileOperations.js';
import type { VideoData, Config } from '../types/index.js';
import { extractFileIdFromDriveLink } from '../utils/driveUtils.js';

export class VideoProcessor {
  constructor(
    private readonly driveService: IGoogleDriveService,
    private readonly youtubeService: IYouTubeService,
    private readonly fileOps: IFileOperations,
    private readonly config: Config
  ) {}

  async processVideo(videoData: VideoData): Promise<string> {
    // Extract file ID
    const fileId = extractFileIdFromDriveLink(videoData.driveLink);
    if (!fileId) {
      throw new Error('Invalid Google Drive link');
    }

    // Ensure temp directory exists
    const tempDir = this.config.tempDir ?? './temp_videos';
    this.fileOps.mkdir(tempDir);

    // Download video
    const tempVideoPath = path.join(tempDir, `${videoData.uniqueId}.mp4`);

    await this.driveService.downloadFile(fileId, tempVideoPath);

    try {
      // Upload to YouTube
      const youtubeId = await this.youtubeService.uploadVideo(
        tempVideoPath,
        videoData,
        (progress) => {
          process.stdout.write(`\rUploading ${videoData.uniqueId}: ${progress.toFixed(2)}%`);
        }
      );

      process.stdout.write('\n'); // New line after progress
      return youtubeId;
    } finally {
      // Clean up temp file
      this.fileOps.unlink(tempVideoPath);
    }
  }
}
