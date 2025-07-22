export interface IGoogleDriveService {
  downloadFile(fileId: string, outputPath: string): Promise<void>;
}
