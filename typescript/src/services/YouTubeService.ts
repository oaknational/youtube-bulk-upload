import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import type { IYouTubeService } from '../interfaces/IYouTubeService.js';
import type { IFileOperations } from '../interfaces/IFileOperations.js';
import type { VideoData } from '../types/index.js';

export class YouTubeService implements IYouTubeService {
  private youtube;

  constructor(
    authClient: OAuth2Client,
    private readonly fileOps: IFileOperations
  ) {
    this.youtube = google.youtube({ version: 'v3', auth: authClient });
  }

  async uploadVideo(
    videoPath: string,
    videoData: VideoData,
    onProgress?: (progress: number) => void
  ): Promise<string> {
    const fileSize = this.fileOps.stat(videoPath).size;

    const response = await this.youtube.videos.insert(
      {
        part: ['snippet', 'status'],
        requestBody: {
          snippet: {
            title: videoData.title,
            description: videoData.description,
            tags: videoData.tags,
            categoryId: '22', // People & Blogs
          },
          status: {
            privacyStatus: 'private',
            selfDeclaredMadeForKids: false,
          },
        },
        media: {
          body: this.fileOps.createReadStream(videoPath),
        },
      },
      {
        onUploadProgress: (evt) => {
          const progress = (evt.bytesRead / fileSize) * 100;
          if (onProgress) onProgress(progress);
        },
      }
    );

    return response.data.id ?? '';
  }
}
