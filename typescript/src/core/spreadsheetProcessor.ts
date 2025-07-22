import type { ILogger } from '../interfaces/ILogger.js';
import type { IProgressTracker } from '../interfaces/IProgressTracker.js';
import type { VideoProcessor } from './VideoProcessor.js';
import { parseVideoRow } from '../utils/dataParser.js';

interface ProcessVideoRowsOptions {
  rows: string[][];
  startRow: number;
  logger: ILogger;
  progressTracker: IProgressTracker;
  videoProcessor: VideoProcessor;
}

export async function processVideoRows(options: ProcessVideoRowsOptions): Promise<void> {
  const { rows, startRow, logger, progressTracker, videoProcessor } = options;

  for (let i = startRow; i < rows.length; i++) {
    const row = rows[i];

    if (!row) {
      logger.log(`Row ${i + 1} is empty, skipping`);
      continue;
    }

    const videoData = parseVideoRow(row);
    if (!videoData) {
      logger.log(`Row ${i + 1} has invalid data, skipping`);
      continue;
    }

    if (progressTracker.isVideoProcessed(videoData.uniqueId)) {
      logger.log(`Skipping already processed video: ${videoData.uniqueId}`);
      continue;
    }

    logger.log(`Processing video ${i + 1}/${rows.length}: ${videoData.uniqueId}`);

    try {
      const youtubeId = await videoProcessor.processVideo(videoData);

      logger.log(`Successfully uploaded: ${videoData.uniqueId} -> YouTube ID: ${youtubeId}`);

      progressTracker.markVideoProcessed(videoData.uniqueId);
      progressTracker.updateLastProcessedRow(i + 1);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logger.error(`Failed to process ${videoData.uniqueId}: ${errorMessage}`);
      progressTracker.markVideoFailed(videoData.uniqueId, errorMessage);
    }

    // Rate limiting delay
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
}
