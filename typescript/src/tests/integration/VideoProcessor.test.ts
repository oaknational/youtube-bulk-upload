import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { VideoProcessor } from '../../core/VideoProcessor.js';
import type { VideoData, Config } from '../../types/index.js';
import type { IGoogleDriveService } from '../../interfaces/IGoogleDriveService.js';
import type { IYouTubeService } from '../../interfaces/IYouTubeService.js';
import type { IFileOperations } from '../../interfaces/IFileOperations.js';

describe('VideoProcessor Integration Tests', () => {
  let processor: VideoProcessor;
  let mockDriveService: IGoogleDriveService;
  let mockYouTubeService: IYouTubeService;
  let mockFileOps: IFileOperations;

  const testVideo: VideoData = {
    driveLink: 'https://drive.google.com/file/d/test-file-id/view',
    title: 'Test Video',
    description: 'Test Description',
    tags: ['test', 'video'],
    uniqueId: 'unique-123'
  };

  const testConfig: Config = {
    clientId: 'test-client',
    clientSecret: 'test-secret',
    redirectUri: 'http://localhost',
    spreadsheetId: 'test-sheet',
    tempDir: 'temp-dir'
  };

  beforeEach(() => {
    vi.clearAllMocks();

    // Create mock services
    mockDriveService = {
      downloadFile: vi.fn().mockResolvedValue(undefined)
    };

    mockYouTubeService = {
      uploadVideo: vi.fn().mockResolvedValue('youtube-video-id')
    };


    mockFileOps = {
      readFile: vi.fn(),
      writeFile: vi.fn(),
      appendFile: vi.fn(),
      exists: vi.fn().mockReturnValue(true),
      unlink: vi.fn(),
      mkdir: vi.fn(),
      createReadStream: vi.fn(),
      createWriteStream: vi.fn(),
      stat: vi.fn()
    };

    // Create processor with correct constructor signature
    processor = new VideoProcessor(
      mockDriveService,
      mockYouTubeService,
      mockFileOps,
      testConfig
    );
  });

  describe('processVideo', () => {
    it('should complete full video processing pipeline', async () => {
      // Mock process.stdout.write
      const mockWrite = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);

      const result = await processor.processVideo(testVideo);

      // Verify directory creation
      expect(mockFileOps.mkdir).toHaveBeenCalledWith('temp-dir');

      // Verify download
      expect(mockDriveService.downloadFile).toHaveBeenCalledWith(
        'test-file-id',
        'temp-dir/unique-123.mp4'
      );

      // Verify upload
      expect(mockYouTubeService.uploadVideo).toHaveBeenCalledWith(
        'temp-dir/unique-123.mp4',
        testVideo,
        expect.any(Function)
      );

      // Verify result
      expect(result).toBe('youtube-video-id');

      // Verify cleanup
      expect(mockFileOps.unlink).toHaveBeenCalledWith('temp-dir/unique-123.mp4');

      mockWrite.mockRestore();
    });

    it('should handle progress updates correctly', async () => {
      const mockWrite = vi.spyOn(process.stdout, 'write').mockImplementation(() => true);
      let capturedUploadProgress: Function;

      (mockYouTubeService.uploadVideo as Mock).mockImplementation(
        (path, data, onProgress) => {
          capturedUploadProgress = onProgress;
          return Promise.resolve('youtube-id');
        }
      );

      await processor.processVideo(testVideo);

      // Simulate upload progress
      capturedUploadProgress!(25);
      capturedUploadProgress!(50);
      capturedUploadProgress!(75);
      capturedUploadProgress!(100);

      expect(mockWrite).toHaveBeenCalledWith('\rUploading unique-123: 25.00%');
      expect(mockWrite).toHaveBeenCalledWith('\rUploading unique-123: 50.00%');
      expect(mockWrite).toHaveBeenCalledWith('\rUploading unique-123: 75.00%');
      expect(mockWrite).toHaveBeenCalledWith('\rUploading unique-123: 100.00%');
      expect(mockWrite).toHaveBeenCalledWith('\n');

      mockWrite.mockRestore();
    });

    it('should handle download failure', async () => {
      (mockDriveService.downloadFile as Mock).mockRejectedValue(
        new Error('Download failed: Network error')
      );

      await expect(processor.processVideo(testVideo)).rejects.toThrow(
        'Download failed: Network error'
      );

      // Should not attempt upload
      expect(mockYouTubeService.uploadVideo).not.toHaveBeenCalled();
      
      // Should not reach cleanup since download failed before try block
      expect(mockFileOps.unlink).not.toHaveBeenCalled();
    });

    it('should handle upload failure', async () => {
      (mockYouTubeService.uploadVideo as Mock).mockRejectedValue(
        new Error('Upload quota exceeded')
      );

      await expect(processor.processVideo(testVideo)).rejects.toThrow(
        'Upload quota exceeded'
      );

      // Should still cleanup
      expect(mockFileOps.unlink).toHaveBeenCalledWith('temp-dir/unique-123.mp4');
    });

    it('should always attempt cleanup even if upload fails', async () => {
      (mockYouTubeService.uploadVideo as Mock).mockRejectedValue(new Error('Upload failed'));

      await expect(processor.processVideo(testVideo)).rejects.toThrow('Upload failed');

      // Should still attempt cleanup
      expect(mockFileOps.unlink).toHaveBeenCalledWith('temp-dir/unique-123.mp4');
    });

    it('should handle videos with special characters in unique ID', async () => {
      const specialVideo: VideoData = {
        ...testVideo,
        uniqueId: 'video with spaces & special/chars'
      };

      await processor.processVideo(specialVideo);

      // Should sanitize filename
      expect(mockDriveService.downloadFile).toHaveBeenCalledWith(
        'test-file-id',
        'temp-dir/video with spaces & special/chars.mp4'
      );
    });

    it('should create temp directory every time', async () => {
      await processor.processVideo(testVideo);

      expect(mockFileOps.mkdir).toHaveBeenCalledWith('temp-dir');
    });

    it('should handle concurrent video processing', async () => {
      const videos: VideoData[] = [
        { ...testVideo, uniqueId: 'video1' },
        { ...testVideo, uniqueId: 'video2' },
        { ...testVideo, uniqueId: 'video3' }
      ];

      // Process videos concurrently
      const results = await Promise.all(
        videos.map(video => processor.processVideo(video))
      );

      // All should complete
      expect(results).toHaveLength(3);
      expect(mockDriveService.downloadFile).toHaveBeenCalledTimes(3);
      expect(mockYouTubeService.uploadVideo).toHaveBeenCalledTimes(3);
      expect(mockFileOps.unlink).toHaveBeenCalledTimes(3);
    });
  });

  describe('extractFileId', () => {
    it('should handle malformed drive links gracefully', async () => {
      const badVideo: VideoData = {
        ...testVideo,
        driveLink: 'not-a-valid-url'
      };

      await expect(processor.processVideo(badVideo)).rejects.toThrow('Invalid Google Drive link');
    });

    it('should handle empty drive link', async () => {
      const badVideo: VideoData = {
        ...testVideo,
        driveLink: ''
      };

      await expect(processor.processVideo(badVideo)).rejects.toThrow('Invalid Google Drive link');
    });
  });
});