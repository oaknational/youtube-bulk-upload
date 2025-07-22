import type { OAuth2Client } from 'google-auth-library';
import type { AuthTokens } from '../types/index.js';

export interface IAuthenticationService {
  initialize(): Promise<OAuth2Client>;
  getAuthUrl(): string;
  getTokensFromCode(code: string): Promise<AuthTokens>;
  saveTokens(tokens: AuthTokens): Promise<void>;
  loadSavedTokens(): Promise<AuthTokens | null>;
  getAuthenticatedClient(): OAuth2Client;
}
