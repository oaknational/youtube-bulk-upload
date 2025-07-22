import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import type { IGoogleDriveService } from '../interfaces/IGoogleDriveService.js';
import type { IFileOperations } from '../interfaces/IFileOperations.js';
import type { ILogger } from '../interfaces/ILogger.js';

export class GoogleDriveService implements IGoogleDriveService {
  private drive;

  constructor(
    authClient: OAuth2Client,
    private readonly fileOps: IFileOperations,
    private readonly logger: ILogger
  ) {
    this.drive = google.drive({ version: 'v3', auth: authClient });
  }

  async downloadFile(fileId: string, outputPath: string): Promise<void> {
    const response = await this.drive.files.get(
      { fileId, alt: 'media' },
      { responseType: 'stream' }
    );

    const dest = this.fileOps.createWriteStream(outputPath);

    return new Promise((resolve, reject) => {
      response.data
        .on('end', () => {
          this.logger.log(`Downloaded file: ${outputPath}`);
          resolve();
        })
        .on('error', (err: Error) => {
          this.logger.error(`Error downloading file: ${err.message}`);
          reject(err);
        })
        .pipe(dest);
    });
  }
}
