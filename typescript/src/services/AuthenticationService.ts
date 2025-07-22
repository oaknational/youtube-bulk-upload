import { google } from 'googleapis';
import type { OAuth2Client } from 'google-auth-library';
import readline from 'readline';
import type { IAuthenticationService } from '../interfaces/IAuthenticationService.js';
import type { IFileOperations } from '../interfaces/IFileOperations.js';
import type { ILogger } from '../interfaces/ILogger.js';
import type { AuthTokens, Config } from '../types/index.js';

export class AuthenticationService implements IAuthenticationService {
  private oauth2Client: OAuth2Client;
  private readonly scopes = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/spreadsheets.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
  ];

  constructor(
    private readonly config: Config,
    private readonly fileOps: IFileOperations,
    private readonly logger: ILogger
  ) {
    this.oauth2Client = new google.auth.OAuth2(
      config.clientId,
      config.clientSecret,
      config.redirectUri
    );
  }

  async initialize(): Promise<OAuth2Client> {
    const savedTokens = await this.loadSavedTokens();

    if (savedTokens) {
      this.oauth2Client.setCredentials(savedTokens);
    } else {
      await this.performOAuthFlow();
    }

    return this.oauth2Client;
  }

  getAuthUrl(): string {
    return this.oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: this.scopes,
    });
  }

  async getTokensFromCode(code: string): Promise<AuthTokens> {
    const { tokens } = await this.oauth2Client.getToken(code);
    const authTokens: AuthTokens = {};

    if (tokens.access_token != null) {
      authTokens.access_token = tokens.access_token;
    }
    if (tokens.refresh_token != null) {
      authTokens.refresh_token = tokens.refresh_token;
    }
    if (tokens.scope != null) {
      authTokens.scope = tokens.scope;
    }
    if (tokens.token_type != null) {
      authTokens.token_type = tokens.token_type;
    }
    if (tokens.expiry_date != null) {
      authTokens.expiry_date = tokens.expiry_date;
    }

    return authTokens;
  }

  async saveTokens(tokens: AuthTokens): Promise<void> {
    const tokenFile = this.config.tokenFile ?? './token.json';
    this.fileOps.writeFile(tokenFile, JSON.stringify(tokens));
    this.oauth2Client.setCredentials(tokens);
  }

  async loadSavedTokens(): Promise<AuthTokens | null> {
    const tokenFile = this.config.tokenFile ?? './token.json';
    const content = this.fileOps.readFile(tokenFile);

    if (!content) return null;

    try {
      return JSON.parse(content) as AuthTokens;
    } catch {
      return null;
    }
  }

  getAuthenticatedClient(): OAuth2Client {
    return this.oauth2Client;
  }

  private async performOAuthFlow(): Promise<void> {
    const authUrl = this.getAuthUrl();
    this.logger.log(`Authorize this app by visiting this url: ${authUrl}`);

    const code = await this.promptForAuthCode();
    const tokens = await this.getTokensFromCode(code);
    await this.saveTokens(tokens);
  }

  private async promptForAuthCode(): Promise<string> {
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
}
