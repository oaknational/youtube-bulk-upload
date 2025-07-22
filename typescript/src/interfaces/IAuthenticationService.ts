import type { OAuth2Client } from 'google-auth-library';
import type { AuthTokens } from '../types/index.js';

/**
 * Interface for OAuth2 authentication service with Google APIs.
 * Handles the authentication flow, token management, and provides authenticated
 * clients for accessing Google services like YouTube, Drive, and Sheets.
 */
export interface IAuthenticationService {
  /**
   * Initializes the authentication service and ensures valid credentials are available.
   * This method handles the complete authentication flow including token refresh if needed.
   * @returns An authenticated OAuth2Client ready for API calls
   * @throws May throw an error if authentication fails or credentials are invalid
   */
  initialize(): Promise<OAuth2Client>;
  
  /**
   * Generates the OAuth2 authorization URL for user consent.
   * Users should be directed to this URL to grant permissions for the required scopes.
   * @returns The authorization URL string that users should visit in their browser
   */
  getAuthUrl(): string;
  
  /**
   * Exchanges an authorization code for access and refresh tokens.
   * This is called after the user grants consent and is redirected back with a code.
   * @param code - The authorization code received from the OAuth2 consent flow
   * @returns The AuthTokens object containing access and refresh tokens
   * @throws May throw an error if the code is invalid or has expired
   */
  getTokensFromCode(code: string): Promise<AuthTokens>;
  
  /**
   * Saves OAuth2 credentials to persistent storage for future use.
   * This allows the application to skip the consent flow on subsequent runs.
   * @param tokens - The AuthTokens object containing Google API credentials to save
   * @throws May throw an error if the tokens cannot be saved to storage
   */
  saveTokens(tokens: AuthTokens): Promise<void>;
  
  /**
   * Loads previously saved OAuth2 credentials from persistent storage.
   * @returns The saved AuthTokens if they exist, or null if no tokens are found
   * @throws May throw an error if the token file exists but cannot be read or parsed
   */
  loadSavedTokens(): Promise<AuthTokens | null>;
  
  /**
   * Retrieves the authenticated OAuth2 client for making API calls.
   * The client must have been initialized first via the initialize() method.
   * @returns The authenticated OAuth2Client instance
   * @throws May throw an error if the client has not been initialized yet
   */
  getAuthenticatedClient(): OAuth2Client;
}
