/**
 * Represents metadata for a single video to be uploaded to YouTube.
 * This data is typically parsed from a row in a Google Sheets spreadsheet.
 * 
 * @example
 * ```typescript
 * const video: VideoData = {
 *   driveLink: "https://drive.google.com/file/d/1abc123/view",
 *   title: "My Tutorial Video - Episode 1",
 *   description: "In this episode, we learn the basics of TypeScript...",
 *   tags: ["tutorial", "typescript", "programming", "beginner"],
 *   uniqueId: "video_001"
 * };
 * ```
 */
export interface VideoData {
  /** 
   * Google Drive shareable link to the video file.
   * Must be a valid Drive URL in one of these formats:
   * - https://drive.google.com/file/d/{fileId}/view
   * - https://drive.google.com/open?id={fileId}
   * - https://drive.google.com/uc?id={fileId}
   */
  driveLink: string;
  
  /** 
   * Video title for YouTube (max 100 characters).
   * This will be displayed as the main title on YouTube.
   */
  title: string;
  
  /** 
   * Video description for YouTube (max 5000 characters).
   * Supports YouTube markdown formatting including links and timestamps.
   */
  description: string;
  
  /** 
   * Array of tags/keywords for the video.
   * Each tag should be 2-30 characters. YouTube allows up to 500 characters total.
   * Tags help with video discovery and SEO.
   */
  tags: string[];
  
  /** 
   * Unique identifier for tracking upload progress.
   * Should be unique across all videos in the spreadsheet.
   * Used to prevent duplicate uploads and track failed attempts.
   */
  uniqueId: string;
}

/**
 * Tracks the progress of bulk upload operations.
 * Persisted to disk to enable resumable uploads and retry functionality.
 * 
 * @example
 * ```typescript
 * const progress: UploadProgress = {
 *   processedIds: new Set(["video_001", "video_002"]),
 *   lastProcessedRow: 3,
 *   failedUploads: [{
 *     uniqueId: "video_003",
 *     error: "Quota exceeded",
 *     timestamp: new Date().toISOString()
 *   }]
 * };
 * ```
 */
export interface UploadProgress {
  /** 
   * Set of unique IDs for successfully uploaded videos.
   * Used to skip already processed videos when resuming.
   */
  processedIds: Set<string>;
  
  /** 
   * The last row number processed from the spreadsheet (1-indexed).
   * Enables resuming from a specific position after interruption.
   */
  lastProcessedRow: number;
  
  /** 
   * Array of videos that failed to upload with error details.
   * Can be used for retry operations or error reporting.
   */
  failedUploads: FailedUpload[];
}

/**
 * Records details about a failed video upload attempt.
 * Used for debugging, retry logic, and error reporting.
 * 
 * @example
 * ```typescript
 * const failure: FailedUpload = {
 *   uniqueId: "video_123",
 *   error: "HttpError 403: The request cannot be completed because you have exceeded your quota.",
 *   timestamp: "2024-12-23T10:30:45.123Z"
 * };
 * ```
 */
export interface FailedUpload {
  /** The unique identifier of the video that failed to upload */
  uniqueId: string;
  
  /** 
   * Error message or stack trace from the failure.
   * Should contain enough detail to diagnose the issue.
   */
  error: string;
  
  /** 
   * ISO 8601 timestamp of when the failure occurred.
   * Used for debugging and determining retry eligibility.
   */
  timestamp: string;
}

/**
 * Application configuration for the YouTube bulk upload tool.
 * Contains OAuth credentials and operational settings.
 * 
 * @example
 * ```typescript
 * const config: Config = {
 *   // OAuth2 credentials from Google Cloud Console
 *   clientId: "123456-abc.apps.googleusercontent.com",
 *   clientSecret: "GOCSPX-secretkey123",
 *   redirectUri: "http://localhost:8080",
 *   
 *   // Spreadsheet containing video metadata
 *   spreadsheetId: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
 *   sheetRange: "Videos!A2:E",  // Optional, defaults to "Sheet1!A:E"
 *   
 *   // File paths (all optional with defaults)
 *   progressFile: "./upload_progress.json",
 *   logFile: "./upload_log.txt",
 *   tokenFile: "./google_auth_tokens.json",
 *   tempDir: "./temp_videos"
 * };
 * ```
 */
export interface Config {
  /** 
   * OAuth2 client ID from Google Cloud Console.
   * Found in the credentials JSON file under "client_id".
   */
  clientId: string;
  
  /** 
   * OAuth2 client secret from Google Cloud Console.
   * Found in the credentials JSON file under "client_secret".
   * Keep this value secure and never commit to version control.
   */
  clientSecret: string;
  
  /** 
   * OAuth2 redirect URI configured in Google Cloud Console.
   * For CLI tools, typically "http://localhost:8080" or similar.
   * Must match exactly what's configured in Google Cloud Console.
   */
  redirectUri: string;
  
  /** 
   * Google Sheets spreadsheet ID containing video metadata.
   * Can be extracted from the spreadsheet URL:
   * https://docs.google.com/spreadsheets/d/{spreadsheetId}/edit
   */
  spreadsheetId: string;
  
  /** 
   * Range in the spreadsheet to read (A1 notation).
   * Examples: "Sheet1!A:E", "Videos!A2:E100", "Sheet1"
   * @default "Sheet1!A:E"
   */
  sheetRange?: string | undefined;
  
  /** 
   * Path to the progress tracking JSON file.
   * Used for resumable uploads and retry functionality.
   * @default "./upload_progress.json"
   */
  progressFile?: string | undefined;
  
  /** 
   * Path to the log file for detailed operation logs.
   * Useful for debugging and audit trails.
   * @default "./upload_log.txt"
   */
  logFile?: string | undefined;
  
  /** 
   * Path to store OAuth2 tokens for persistent authentication.
   * Tokens are encrypted and should not be shared.
   * @default "./google_auth_tokens.json"
   */
  tokenFile?: string | undefined;
  
  /** 
   * Directory for temporarily storing downloaded videos.
   * Videos are deleted after successful upload.
   * @default "./temp_videos"
   */
  tempDir?: string | undefined;
}

/**
 * OAuth2 tokens returned by Google's authentication flow.
 * These tokens provide access to Google APIs on behalf of the user.
 * 
 * @example
 * ```typescript
 * const tokens: AuthTokens = {
 *   access_token: "ya29.a0AfH6SMBx...",  // Short-lived (1 hour)
 *   refresh_token: "1//0g6X7...",         // Long-lived, used to get new access tokens
 *   scope: "https://www.googleapis.com/auth/youtube.upload ...",
 *   token_type: "Bearer",
 *   expiry_date: 1703342445000  // Unix timestamp in milliseconds
 * };
 * ```
 * 
 * @see https://developers.google.com/identity/protocols/oauth2
 */
export interface AuthTokens {
  /** 
   * Short-lived token (typically 1 hour) used to authenticate API requests.
   * Must be included in the Authorization header as "Bearer {token}".
   */
  access_token?: string;
  
  /** 
   * Long-lived token used to obtain new access tokens when they expire.
   * Only provided on first authorization or when access_type=offline.
   * Store this securely as it won't be provided again.
   */
  refresh_token?: string;
  
  /** 
   * Space-delimited list of OAuth2 scopes granted by the user.
   * For this tool, typically includes:
   * - https://www.googleapis.com/auth/youtube.upload
   * - https://www.googleapis.com/auth/drive.readonly
   * - https://www.googleapis.com/auth/spreadsheets.readonly
   */
  scope?: string;
  
  /** 
   * The type of token returned. Always "Bearer" for Google OAuth2.
   * Used in Authorization header: "Authorization: Bearer {access_token}"
   */
  token_type?: string;
  
  /** 
   * Unix timestamp (milliseconds) when the access token expires.
   * Used to determine when to refresh the token (ideally before expiry).
   * Typically set to current time + 3600 seconds (1 hour).
   */
  expiry_date?: number;
}
