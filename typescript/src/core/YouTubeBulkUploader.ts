import type { IAuthenticationService } from '../interfaces/IAuthenticationService.js';
import type { IGoogleSheetsService } from '../interfaces/IGoogleSheetsService.js';
import type { IProgressTracker } from '../interfaces/IProgressTracker.js';
import type { ILogger } from '../interfaces/ILogger.js';
import type { Config } from '../types/index.js';
import type { VideoProcessor } from './VideoProcessor.js';
import { processVideoRows } from './spreadsheetProcessor.js';

export class YouTubeBulkUploader {
  constructor(
    private readonly authService: IAuthenticationService,
    private readonly sheetsService: IGoogleSheetsService,
    private readonly videoProcessor: VideoProcessor,
    private readonly progressTracker: IProgressTracker,
    private readonly logger: ILogger,
    private readonly config: Config
  ) {}

  async initialize(): Promise<void> {
    await this.authService.initialize();
  }

  async processSpreadsheet(): Promise<void> {
    try {
      const rows = await this.fetchSpreadsheetRows();

      if (rows.length === 0) {
        this.logger.log('No data found in spreadsheet');
        return;
      }

      const progress = this.progressTracker.getProgress();
      const startRow = Math.max(1, progress.lastProcessedRow);

      await processVideoRows({
        rows,
        startRow,
        logger: this.logger,
        progressTracker: this.progressTracker,
        videoProcessor: this.videoProcessor,
      });

      this.logFinalStats();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      this.logger.error(`Fatal error: ${errorMessage}`);
      throw error;
    }
  }

  private async fetchSpreadsheetRows(): Promise<string[][]> {
    return await this.sheetsService.fetchSpreadsheetData(
      this.config.spreadsheetId,
      this.config.sheetRange ?? 'Sheet1!A:E'
    );
  }

  private logFinalStats(): void {
    const finalProgress = this.progressTracker.getProgress();
    this.logger.log('Upload process completed!');
    this.logger.log(`Total processed: ${finalProgress.processedIds.size}`);
    this.logger.log(`Failed uploads: ${finalProgress.failedUploads.length}`);
  }

  async retryFailedUploads(): Promise<void> {
    const progress = this.progressTracker.getProgress();
    const failedUploads = [...progress.failedUploads];

    // Clear failed uploads list
    progress.failedUploads = [];
    this.progressTracker.saveProgress(progress);

    this.logger.log(`Retrying ${failedUploads.length} failed uploads...`);

    // Remove failed videos from processed list so they can be retried
    for (const failed of failedUploads) {
      progress.processedIds.delete(failed.uniqueId);
    }

    this.progressTracker.saveProgress(progress);

    // Re-process the spreadsheet - it will skip successful uploads and retry failed ones
    await this.processSpreadsheet();
  }
}
