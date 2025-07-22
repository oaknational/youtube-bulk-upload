import { google } from 'googleapis';
import type { Config } from '../types/index.js';
import { FileOperations } from '../services/FileOperations.js';
import { Logger } from '../services/Logger.js';
import { AuthenticationService } from '../services/AuthenticationService.js';
import { GoogleSheetsService } from '../services/GoogleSheetsService.js';
import { GoogleDriveService } from '../services/GoogleDriveService.js';
import { YouTubeService } from '../services/YouTubeService.js';
import { ProgressTracker } from '../services/ProgressTracker.js';
import { VideoProcessor } from './VideoProcessor.js';
import { YouTubeBulkUploader } from './YouTubeBulkUploader.js';

export class DependencyContainer {
  private fileOps: FileOperations;
  private logger: Logger;
  private authService: AuthenticationService;
  private sheetsService?: GoogleSheetsService;
  private driveService?: GoogleDriveService;
  private youtubeService?: YouTubeService;
  private progressTracker: ProgressTracker;
  private videoProcessor?: VideoProcessor;

  constructor(private readonly config: Config) {
    this.fileOps = new FileOperations();
    this.logger = new Logger(config.logFile ?? './upload_log.txt', this.fileOps);
    this.authService = new AuthenticationService(config, this.fileOps, this.logger);
    this.progressTracker = new ProgressTracker(
      config.progressFile ?? './upload_progress.json',
      this.fileOps
    );
  }

  async createYouTubeBulkUploader(): Promise<YouTubeBulkUploader> {
    // Initialize authentication first
    const authClient = await this.authService.initialize();

    // Set up Google API authentication globally
    google.options({ auth: authClient });

    // Create services with authenticated client
    this.sheetsService = new GoogleSheetsService(authClient);
    this.driveService = new GoogleDriveService(authClient, this.fileOps, this.logger);
    this.youtubeService = new YouTubeService(authClient, this.fileOps);

    // Create video processor
    this.videoProcessor = new VideoProcessor(
      this.driveService,
      this.youtubeService,
      this.fileOps,
      this.config
    );

    // Create and return the main uploader
    return new YouTubeBulkUploader(
      this.authService,
      this.sheetsService,
      this.videoProcessor,
      this.progressTracker,
      this.logger,
      this.config
    );
  }
}
