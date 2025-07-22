import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import * as fs from 'fs';
import * as path from 'path';
import * as readline from 'readline';

// Interfaces
export interface VideoData {
  driveLink: string;
  title: string;
  description: string;
  tags: string[];
  uniqueId: string;
}

export interface UploadProgress {
  processedIds: Set<string>;
  lastProcessedRow: number;
  failedUploads: {
    uniqueId: string;
    error: string;
    timestamp: string;
  }[];
}

export interface Config {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  spreadsheetId: string;
  sheetRange?: string | undefined;
  progressFile?: string | undefined;
  logFile?: string | undefined;
  tokenFile?: string | undefined;
  tempDir?: string | undefined;
}

export interface Services {
  sheets: any;
  drive: any;
  youtube: any;
}

// Pure utility functions
export function extractFileIdFromDriveLink(link: string): string | null {
  const patterns = [
    /\/file\/d\/([a-zA-Z0-9-_]+)/,
    /id=([a-zA-Z0-9-_]+)/,
    /\/open\?id=([a-zA-Z0-9-_]+)/,
  ];

  for (const pattern of patterns) {
    const match = link.match(pattern);
    if (match?.[1]) return match[1];
  }

  return null;
}

export function parseVideoRow(row: string[]): VideoData | null {
  if (row.length < 5) return null;

  const [driveLink, title, description, tagString, uniqueId] = row;

  if (!driveLink || !title || !description || !uniqueId) {
    return null;
  }

  return {
    driveLink,
    title,
    description,
    tags: tagString ? tagString.split(',').map((tag) => tag.trim()) : [],
    uniqueId,
  };
}

export function createLogMessage(message: string): string {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] ${message}\n`;
}

export function serializeProgress(progress: UploadProgress): string {
  const data = {
    processedIds: Array.from(progress.processedIds),
    lastProcessedRow: progress.lastProcessedRow,
    failedUploads: progress.failedUploads,
  };
  return JSON.stringify(data, null, 2);
}

export function deserializeProgress(data: string): UploadProgress {
  try {
    const parsed = JSON.parse(data);
    return {
      processedIds: new Set(parsed.processedIds || []),
      lastProcessedRow: parsed.lastProcessedRow || 0,
      failedUploads: parsed.failedUploads || [],
    };
  } catch {
    return {
      processedIds: new Set(),
      lastProcessedRow: 0,
      failedUploads: [],
    };
  }
}

// File system operations
export const fileOperations = {
  readFile: (path: string): string | null => {
    try {
      return fs.readFileSync(path, 'utf8');
    } catch {
      return null;
    }
  },

  writeFile: (path: string, content: string): void => {
    fs.writeFileSync(path, content);
  },

  appendFile: (path: string, content: string): void => {
    fs.appendFileSync(path, content);
  },

  exists: (path: string): boolean => {
    return fs.existsSync(path);
  },

  unlink: (path: string): void => {
    fs.unlinkSync(path);
  },

  mkdir: (path: string): void => {
    if (!fs.existsSync(path)) {
      fs.mkdirSync(path);
    }
  },

  createReadStream: (path: string): fs.ReadStream => {
    return fs.createReadStream(path);
  },

  createWriteStream: (path: string): fs.WriteStream => {
    return fs.createWriteStream(path);
  },

  stat: (path: string): fs.Stats => {
    return fs.statSync(path);
  },
};

// Progress management functions
export function loadProgress(progressFile: string, fileOps = fileOperations): UploadProgress {
  const content = fileOps.readFile(progressFile);
  if (!content) {
    return {
      processedIds: new Set(),
      lastProcessedRow: 0,
      failedUploads: [],
    };
  }
  return deserializeProgress(content);
}

export function saveProgress(
  progressFile: string,
  progress: UploadProgress,
  fileOps = fileOperations
): void {
  fileOps.writeFile(progressFile, serializeProgress(progress));
}

// Logging functions
export function log(
  message: string,
  logFile: string,
  fileOps = fileOperations,
  logger = console.log
): void {
  const logMessage = createLogMessage(message);
  logger(logMessage.trim());
  fileOps.appendFile(logFile, logMessage);
}

// OAuth functions
export async function createOAuth2Client(config: Config): Promise<OAuth2Client> {
  return new google.auth.OAuth2(config.clientId, config.clientSecret, config.redirectUri);
}

export async function loadSavedToken(
  tokenFile: string,
  fileOps = fileOperations
): Promise<any | null> {
  const content = fileOps.readFile(tokenFile);
  if (!content) return null;

  try {
    return JSON.parse(content);
  } catch {
    return null;
  }
}

export async function getAuthCode(authUrl: string): Promise<string> {
  console.log('Authorize this app by visiting this url:', authUrl);
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  return new Promise<string>((resolve) => {
    rl.question('Enter the code from that page here: ', (code) => {
      rl.close();
      resolve(code);
    });
  });
}

// Google API operations
export async function downloadVideoFromDrive(
  fileId: string,
  outputPath: string,
  driveService: any,
  fileOps = fileOperations,
  logger?: (msg: string) => void
): Promise<void> {
  const response = await driveService.files.get(
    { fileId, alt: 'media' },
    { responseType: 'stream' }
  );

  const dest = fileOps.createWriteStream(outputPath);

  return new Promise((resolve, reject) => {
    response.data
      .on('end', () => {
        if (logger) logger(`Downloaded file: ${outputPath}`);
        resolve();
      })
      .on('error', (err: any) => {
        if (logger) logger(`Error downloading file: ${err}`);
        reject(err);
      })
      .pipe(dest);
  });
}

export async function uploadVideoToYouTube(
  videoPath: string,
  videoData: VideoData,
  youtubeService: any,
  fileOps = fileOperations,
  onProgress?: (progress: number) => void
): Promise<string> {
  const fileSize = fileOps.stat(videoPath).size;

  const response = await youtubeService.videos.insert(
    {
      part: ['snippet', 'status'],
      requestBody: {
        snippet: {
          title: videoData.title,
          description: videoData.description,
          tags: videoData.tags,
          categoryId: '22',
        },
        status: {
          privacyStatus: 'private',
          selfDeclaredMadeForKids: false,
        },
      },
      media: {
        body: fileOps.createReadStream(videoPath),
      },
    },
    {
      onUploadProgress: (evt: any) => {
        const progress = (evt.bytesRead / fileSize) * 100;
        if (onProgress) onProgress(progress);
      },
    }
  );

  return response.data.id || '';
}

export async function fetchSpreadsheetData(
  spreadsheetId: string,
  range: string,
  sheetsService: any
): Promise<string[][]> {
  const response = await sheetsService.spreadsheets.values.get({
    spreadsheetId,
    range,
  });

  return response.data.values || [];
}

// Main processing function
export async function processVideo(
  videoData: VideoData,
  services: Services,
  config: Config,
  fileOps = fileOperations,
  logger?: (msg: string) => void
): Promise<string> {
  // Extract file ID
  const fileId = extractFileIdFromDriveLink(videoData.driveLink);
  if (!fileId) {
    throw new Error('Invalid Google Drive link');
  }

  // Ensure temp directory exists
  fileOps.mkdir(config.tempDir || './temp_videos');

  // Download video
  const tempVideoPath = path.join(config.tempDir || './temp_videos', `${videoData.uniqueId}.mp4`);

  await downloadVideoFromDrive(fileId, tempVideoPath, services.drive, fileOps, logger);

  try {
    // Upload to YouTube
    const youtubeId = await uploadVideoToYouTube(
      tempVideoPath,
      videoData,
      services.youtube,
      fileOps,
      (progress) => {
        process.stdout.write(`\rUploading ${videoData.uniqueId}: ${progress.toFixed(2)}%`);
      }
    );

    console.log(''); // New line after progress
    return youtubeId;
  } finally {
    // Clean up temp file
    fileOps.unlink(tempVideoPath);
  }
}

// Main class refactored to use pure functions
export class YouTubeBulkUploader {
  private oauth2Client: OAuth2Client;
  private services: Services;

  constructor(
    private config: Config,
    private fileOps = fileOperations
  ) {
    this.oauth2Client = new google.auth.OAuth2(
      config.clientId,
      config.clientSecret,
      config.redirectUri
    );
    this.services = {
      sheets: google.sheets('v4'),
      drive: google.drive('v3'),
      youtube: google.youtube('v3'),
    };
  }

  async initialize(): Promise<void> {
    const tokenFile = this.config.tokenFile || './token.json';
    const token = await loadSavedToken(tokenFile, this.fileOps);

    if (token) {
      this.oauth2Client.setCredentials(token);
    } else {
      await this.authenticate();
    }

    google.options({ auth: this.oauth2Client });
  }

  private async authenticate(): Promise<void> {
    const authUrl = this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly',
      ],
    });

    const code = await getAuthCode(authUrl);
    const { tokens } = await this.oauth2Client.getToken(code);
    this.oauth2Client.setCredentials(tokens);

    this.fileOps.writeFile(this.config.tokenFile || './token.json', JSON.stringify(tokens));
  }

  async processSpreadsheet(): Promise<void> {
    const progressFile = this.config.progressFile || './upload_progress.json';
    const logFile = this.config.logFile || './upload_log.txt';
    const progress = loadProgress(progressFile, this.fileOps);

    const logger = (msg: string) => log(msg, logFile, this.fileOps);

    try {
      const rows = await fetchSpreadsheetData(
        this.config.spreadsheetId,
        this.config.sheetRange || 'Sheet1!A:E',
        this.services.sheets
      );

      if (!rows || rows.length === 0) {
        logger('No data found in spreadsheet');
        return;
      }

      const startRow = Math.max(1, progress.lastProcessedRow);

      for (let i = startRow; i < rows.length; i++) {
        const row = rows[i];
        if (!row) {
          logger(`Row ${i + 1} is empty, skipping`);
          continue;
        }

        const videoData = parseVideoRow(row);
        if (!videoData) {
          logger(`Row ${i + 1} has invalid data, skipping`);
          continue;
        }

        if (progress.processedIds.has(videoData.uniqueId)) {
          logger(`Skipping already processed video: ${videoData.uniqueId}`);
          continue;
        }

        logger(`Processing video ${i + 1}/${rows.length}: ${videoData.uniqueId}`);

        try {
          const youtubeId = await processVideo(
            videoData,
            this.services,
            this.config,
            this.fileOps,
            logger
          );

          logger(`Successfully uploaded: ${videoData.uniqueId} -> YouTube ID: ${youtubeId}`);

          progress.processedIds.add(videoData.uniqueId);
          progress.lastProcessedRow = i + 1;
          saveProgress(progressFile, progress, this.fileOps);
        } catch (error) {
          logger(`Failed to process ${videoData.uniqueId}: ${error}`);
          progress.failedUploads.push({
            uniqueId: videoData.uniqueId,
            error: String(error),
            timestamp: new Date().toISOString(),
          });
          saveProgress(progressFile, progress, this.fileOps);
        }

        // Rate limiting delay
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }

      logger('Upload process completed!');
      logger(`Total processed: ${progress.processedIds.size}`);
      logger(`Failed uploads: ${progress.failedUploads.length}`);
    } catch (error) {
      logger(`Fatal error: ${error}`);
      throw error;
    }
  }

  async retryFailedUploads(): Promise<void> {
    const progressFile = this.config.progressFile || './upload_progress.json';
    const logFile = this.config.logFile || './upload_log.txt';
    const progress = loadProgress(progressFile, this.fileOps);

    const logger = (msg: string) => log(msg, logFile, this.fileOps);

    const failedUploads = [...progress.failedUploads];
    progress.failedUploads = [];

    logger(`Retrying ${failedUploads.length} failed uploads...`);

    for (const failed of failedUploads) {
      progress.processedIds.delete(failed.uniqueId);
    }

    saveProgress(progressFile, progress, this.fileOps);
  }
}

// Main execution function
export async function main(args: string[] = process.argv): Promise<void> {
  const config: Config = {
    clientId: process.env['CLIENT_ID'] || '',
    clientSecret: process.env['CLIENT_SECRET'] || '',
    redirectUri: process.env['REDIRECT_URI'] || '',
    spreadsheetId: process.env['SPREADSHEET_ID'] || '',
    sheetRange: process.env['SHEET_RANGE'],
    progressFile: process.env['PROGRESS_FILE'],
    logFile: process.env['LOG_FILE'],
    tokenFile: process.env['TOKEN_FILE'],
    tempDir: process.env['TEMP_DIR'],
  };

  // Validate config
  const requiredFields: (keyof Config)[] = [
    'clientId',
    'clientSecret',
    'redirectUri',
    'spreadsheetId',
  ];
  for (const field of requiredFields) {
    if (!config[field]) {
      console.error(`Missing required environment variable: ${field.toUpperCase()}`);
      process.exit(1);
    }
  }

  const uploader = new YouTubeBulkUploader(config);

  try {
    await uploader.initialize();

    if (args.includes('--retry-failed')) {
      await uploader.retryFailedUploads();
    }

    await uploader.processSpreadsheet();
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Only run main if this is the entry point
if (require.main === module) {
  main();
}
