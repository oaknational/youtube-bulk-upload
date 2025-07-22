import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { YouTubeService } from '../YouTubeService.js';
import type { OAuth2Client } from 'google-auth-library';
import type { IFileOperations } from '../../interfaces/IFileOperations.js';
import type { VideoData } from '../../types/index.js';
import type { ReadStream, Stats } from 'fs';

// Mock the YouTube API
const mockInsert = vi.fn();
const mockYouTube = {
  videos: {
    insert: mockInsert
  }
};

// Mock googleapis
vi.mock('googleapis', () => ({
  google: {
    youtube: vi.fn(() => mockYouTube)
  }
}));

describe('YouTubeService', () => {
  let youtubeService: YouTubeService;
  let mockAuthClient: OAuth2Client;
  let mockFileOps: IFileOperations;
  let mockReadStream: ReadStream;
  let mockStats: Stats;

  const testVideoData: VideoData = {
    driveLink: 'https://drive.google.com/file/d/test-id',
    title: 'Test Video Title',
    description: 'Test video description',
    tags: ['test', 'video', 'upload'],
    uniqueId: 'unique-123'
  };

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Create mock auth client
    mockAuthClient = {} as OAuth2Client;

    // Create mock read stream
    mockReadStream = {} as ReadStream;

    // Create mock stats
    mockStats = {
      size: 1024 * 1024 * 50 // 50MB
    } as Stats;

    // Setup file operations mock
    mockFileOps = {
      readFile: vi.fn(),
      writeFile: vi.fn(),
      appendFile: vi.fn(),
      exists: vi.fn(),
      unlink: vi.fn(),
      mkdir: vi.fn(),
      createReadStream: vi.fn().mockReturnValue(mockReadStream),
      createWriteStream: vi.fn(),
      stat: vi.fn().mockReturnValue(mockStats)
    };

    // Create service instance
    youtubeService = new YouTubeService(mockAuthClient, mockFileOps);
  });

  describe('constructor', () => {
    it('should initialize YouTube API with auth client', async () => {
      const { google } = await import('googleapis');
      expect(google.youtube).toHaveBeenCalledWith({
        version: 'v3',
        auth: mockAuthClient
      });
    });
  });

  describe('uploadVideo', () => {
    it('should upload video successfully', async () => {
      mockInsert.mockResolvedValue({
        data: {
          id: 'uploaded-video-id-123',
          snippet: { title: 'Test Video Title' }
        }
      });

      const result = await youtubeService.uploadVideo(
        '/path/to/video.mp4',
        testVideoData
      );

      expect(mockFileOps.stat).toHaveBeenCalledWith('/path/to/video.mp4');
      expect(mockFileOps.createReadStream).toHaveBeenCalledWith('/path/to/video.mp4');
      
      expect(mockInsert).toHaveBeenCalledWith(
        {
          part: ['snippet', 'status'],
          requestBody: {
            snippet: {
              title: 'Test Video Title',
              description: 'Test video description',
              tags: ['test', 'video', 'upload'],
              categoryId: '22'
            },
            status: {
              privacyStatus: 'private',
              selfDeclaredMadeForKids: false
            }
          },
          media: {
            body: mockReadStream
          }
        },
        expect.objectContaining({
          onUploadProgress: expect.any(Function)
        })
      );

      expect(result).toBe('uploaded-video-id-123');
    });

    it('should handle upload progress callback', async () => {
      const progressCallback = vi.fn();
      let capturedProgressHandler: Function;

      mockInsert.mockImplementation((params, options) => {
        capturedProgressHandler = options.onUploadProgress;
        return Promise.resolve({
          data: { id: 'video-123' }
        });
      });

      await youtubeService.uploadVideo(
        '/path/to/video.mp4',
        testVideoData,
        progressCallback
      );

      // Simulate progress events
      capturedProgressHandler!({ bytesRead: 0 });
      capturedProgressHandler!({ bytesRead: 26214400 }); // 25MB (50%)
      capturedProgressHandler!({ bytesRead: 52428800 }); // 50MB (100%)

      expect(progressCallback).toHaveBeenCalledTimes(3);
      expect(progressCallback).toHaveBeenNthCalledWith(1, 0);
      expect(progressCallback).toHaveBeenNthCalledWith(2, 50);
      expect(progressCallback).toHaveBeenNthCalledWith(3, 100);
    });

    it('should upload without progress callback', async () => {
      mockInsert.mockResolvedValue({
        data: { id: 'video-456' }
      });

      const result = await youtubeService.uploadVideo(
        '/path/to/video.mp4',
        testVideoData
        // No progress callback
      );

      expect(result).toBe('video-456');
      
      // Get the progress handler
      const options = mockInsert.mock.calls[0][1];
      
      // Should not throw when called without callback
      expect(() => {
        options.onUploadProgress({ bytesRead: 1000 });
      }).not.toThrow();
    });

    it('should handle empty video ID in response', async () => {
      mockInsert.mockResolvedValue({
        data: {
          // No id field
          snippet: { title: 'Test Video' }
        }
      });

      const result = await youtubeService.uploadVideo(
        '/path/to/video.mp4',
        testVideoData
      );

      expect(result).toBe('');
    });

    it('should handle null video ID in response', async () => {
      mockInsert.mockResolvedValue({
        data: {
          id: null
        }
      });

      const result = await youtubeService.uploadVideo(
        '/path/to/video.mp4',
        testVideoData
      );

      expect(result).toBe('');
    });

    it('should handle upload errors', async () => {
      mockInsert.mockRejectedValue(new Error('Upload failed: quota exceeded'));

      await expect(
        youtubeService.uploadVideo('/path/to/video.mp4', testVideoData)
      ).rejects.toThrow('Upload failed: quota exceeded');
    });

    it('should handle stat errors', async () => {
      (mockFileOps.stat as Mock).mockImplementation(() => {
        throw new Error('File not found');
      });

      await expect(
        youtubeService.uploadVideo('/path/to/nonexistent.mp4', testVideoData)
      ).rejects.toThrow('File not found');

      expect(mockInsert).not.toHaveBeenCalled();
    });

    it('should handle videos with special characters in metadata', async () => {
      const specialVideoData: VideoData = {
        ...testVideoData,
        title: 'Video with "quotes" and \'apostrophes\'',
        description: 'Description with\nnewlines\tand\ttabs',
        tags: ['tag with spaces', 'émoji 🎥', 'special/chars']
      };

      mockInsert.mockResolvedValue({
        data: { id: 'special-video-id' }
      });

      await youtubeService.uploadVideo('/path/to/video.mp4', specialVideoData);

      expect(mockInsert).toHaveBeenCalledWith(
        expect.objectContaining({
          requestBody: expect.objectContaining({
            snippet: expect.objectContaining({
              title: 'Video with "quotes" and \'apostrophes\'',
              description: 'Description with\nnewlines\tand\ttabs',
              tags: ['tag with spaces', 'émoji 🎥', 'special/chars']
            })
          })
        }),
        expect.any(Object)
      );
    });

    it('should handle very large files', async () => {
      const largeFileStats = {
        size: 1024 * 1024 * 1024 * 5 // 5GB
      } as Stats;
      (mockFileOps.stat as Mock).mockReturnValue(largeFileStats);

      mockInsert.mockResolvedValue({
        data: { id: 'large-video-id' }
      });

      const result = await youtubeService.uploadVideo(
        '/path/to/large-video.mp4',
        testVideoData
      );

      expect(result).toBe('large-video-id');
    });

    it('should handle empty tags array', async () => {
      const videoDataNoTags: VideoData = {
        ...testVideoData,
        tags: []
      };

      mockInsert.mockResolvedValue({
        data: { id: 'no-tags-video-id' }
      });

      await youtubeService.uploadVideo('/path/to/video.mp4', videoDataNoTags);

      expect(mockInsert).toHaveBeenCalledWith(
        expect.objectContaining({
          requestBody: expect.objectContaining({
            snippet: expect.objectContaining({
              tags: []
            })
          })
        }),
        expect.any(Object)
      );
    });

    it('should handle network interruption errors', async () => {
      const networkError = new Error('Network connection lost');
      (networkError as any).code = 'ENETWORK';
      mockInsert.mockRejectedValue(networkError);

      await expect(
        youtubeService.uploadVideo('/path/to/video.mp4', testVideoData)
      ).rejects.toThrow('Network connection lost');
    });

    it('should calculate progress correctly for different file sizes', async () => {
      const progressCallback = vi.fn();
      let capturedProgressHandler: Function;

      mockInsert.mockImplementation((params, options) => {
        capturedProgressHandler = options.onUploadProgress;
        return Promise.resolve({ data: { id: 'test-id' } });
      });

      // Test with 100MB file
      const largeStats = { size: 1024 * 1024 * 100 } as Stats;
      (mockFileOps.stat as Mock).mockReturnValue(largeStats);

      await youtubeService.uploadVideo(
        '/path/to/video.mp4',
        testVideoData,
        progressCallback
      );

      // Test various progress points
      capturedProgressHandler!({ bytesRead: 10485760 }); // 10MB = 10%
      capturedProgressHandler!({ bytesRead: 52428800 }); // 50MB = 50%
      capturedProgressHandler!({ bytesRead: 104857600 }); // 100MB = 100%

      expect(progressCallback).toHaveBeenNthCalledWith(1, 10);
      expect(progressCallback).toHaveBeenNthCalledWith(2, 50);
      expect(progressCallback).toHaveBeenNthCalledWith(3, 100);
    });
  });
});