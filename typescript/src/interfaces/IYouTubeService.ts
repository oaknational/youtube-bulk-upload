import type { VideoData } from '../types/index.js';

export interface IYouTubeService {
  uploadVideo(
    videoPath: string,
    videoData: VideoData,
    onProgress?: (progress: number) => void
  ): Promise<string>;
}
