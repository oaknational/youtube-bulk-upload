import type { VideoData } from '../types/index.js';

/**
 * Interface for YouTube API operations.
 * Provides methods for uploading videos to YouTube with metadata and progress tracking.
 */
export interface IYouTubeService {
  /**
   * Uploads a video file to YouTube with the specified metadata.
   * @param videoPath - The local file path of the video to upload
   * @param videoData - The metadata for the video including title, description, tags, etc.
   * @param onProgress - Optional callback function that receives upload progress as a percentage (0-100)
   * @returns The YouTube video ID of the uploaded video
   * @throws May throw an error if the upload fails, quota is exceeded, or authentication fails
   */
  uploadVideo(
    videoPath: string,
    videoData: VideoData,
    onProgress?: (progress: number) => void
  ): Promise<string>;
}
