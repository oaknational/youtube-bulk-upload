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
  failedUploads: FailedUpload[];
}

export interface FailedUpload {
  uniqueId: string;
  error: string;
  timestamp: string;
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

export interface AuthTokens {
  access_token?: string;
  refresh_token?: string;
  scope?: string;
  token_type?: string;
  expiry_date?: number;
}
