/**
 * Interface for Google Drive API operations.
 * Provides methods for interacting with Google Drive, particularly for
 * downloading video files stored in Drive for upload to YouTube.
 * 
 * @example
 * ```typescript
 * // Example implementation usage
 * const driveService: IGoogleDriveService = new GoogleDriveService(authClient);
 * 
 * // Download a video file from Google Drive
 * try {
 *   await driveService.downloadFile(
 *     '1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms',
 *     './temp_videos/tutorial_video.mp4'
 *   );
 *   console.log('Video downloaded successfully');
 * } catch (error) {
 *   console.error('Download failed:', error);
 * }
 * ```
 * 
 * @see https://developers.google.com/drive/api/v3/reference/files/get
 */
export interface IGoogleDriveService {
  /**
   * Downloads a file from Google Drive to the local file system.
   * This method handles large files efficiently using streams and provides
   * automatic retry logic for network failures.
   * 
   * @param fileId - The Google Drive file ID to download. Can be extracted from:
   *   - Share URL: https://drive.google.com/file/d/{fileId}/view
   *   - Open URL: https://drive.google.com/open?id={fileId}
   * @param outputPath - The local file path where the downloaded file should be saved.
   *   Parent directory will be created if it doesn't exist.
   * 
   * @returns Promise that resolves when the download is complete
   * 
   * @throws {Error} When the file doesn't exist or isn't accessible:
   *   - "File not found" - The file ID is invalid or file was deleted
   *   - "Permission denied" - The file isn't shared or requires authentication
   *   - "Quota exceeded" - Google Drive API quota has been exceeded
   *   - "Network error" - Connection failed during download
   * 
   * @example
   * ```typescript
   * // Download with error handling
   * try {
   *   await driveService.downloadFile('abc123', '/tmp/video.mp4');
   * } catch (error) {
   *   if (error.message.includes('Permission denied')) {
   *     console.log('Please ensure the file is shared publicly or with your account');
   *   }
   * }
   * 
   * // Extract file ID from various URL formats
   * const urls = [
   *   'https://drive.google.com/file/d/1ABC123/view?usp=sharing',
   *   'https://drive.google.com/open?id=1ABC123',
   *   'https://drive.google.com/uc?id=1ABC123&export=download'
   * ];
   * const fileId = extractFileIdFromDriveLink(urls[0]); // '1ABC123'
   * await driveService.downloadFile(fileId, './videos/downloaded.mp4');
   * ```
   */
  downloadFile(fileId: string, outputPath: string): Promise<void>;
}
