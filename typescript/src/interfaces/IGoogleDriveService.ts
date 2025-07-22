/**
 * Interface for Google Drive API operations.
 * Provides methods for interacting with Google Drive, particularly for
 * downloading video files stored in Drive for upload to YouTube.
 */
export interface IGoogleDriveService {
  /**
   * Downloads a file from Google Drive to the local file system.
   * @param fileId - The Google Drive file ID to download
   * @param outputPath - The local file path where the downloaded file should be saved
   * @throws May throw an error if the file doesn't exist, access is denied, or download fails
   */
  downloadFile(fileId: string, outputPath: string): Promise<void>;
}
