import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { AuthenticationService } from '../AuthenticationService.js';
import type { IFileOperations } from '../../interfaces/IFileOperations.js';
import type { ILogger } from '../../interfaces/ILogger.js';
import type { Config, AuthTokens } from '../../types/index.js';
import readline from 'readline';

// Mock googleapis
const mockOAuth2Client = {
  generateAuthUrl: vi.fn(),
  getToken: vi.fn(),
  setCredentials: vi.fn()
};

vi.mock('googleapis', () => ({
  google: {
    auth: {
      OAuth2: vi.fn(() => mockOAuth2Client)
    }
  }
}));

// Mock readline
vi.mock('readline', () => ({
  default: {
    createInterface: vi.fn(() => ({
      question: vi.fn(),
      close: vi.fn()
    }))
  }
}));

describe('AuthenticationService', () => {
  let authService: AuthenticationService;
  let mockFileOps: IFileOperations;
  let mockLogger: ILogger;
  let mockConfig: Config;
  let mockReadlineInterface: any;

  const defaultTokens: AuthTokens = {
    access_token: 'test-access-token',
    refresh_token: 'test-refresh-token',
    scope: 'test-scope',
    token_type: 'Bearer',
    expiry_date: 1234567890
  };

  beforeEach(() => {
    // Reset all mocks
    vi.clearAllMocks();

    // Setup file operations mock
    mockFileOps = {
      readFile: vi.fn(),
      writeFile: vi.fn(),
      appendFile: vi.fn(),
      exists: vi.fn(),
      unlink: vi.fn(),
      mkdir: vi.fn(),
      createReadStream: vi.fn(),
      createWriteStream: vi.fn(),
      stat: vi.fn()
    };

    // Setup logger mock
    mockLogger = {
      log: vi.fn(),
      error: vi.fn(),
      warn: vi.fn()
    };

    // Setup config
    mockConfig = {
      clientId: 'test-client-id',
      clientSecret: 'test-client-secret',
      redirectUri: 'http://localhost:3000/callback',
      spreadsheetId: 'test-spreadsheet-id',
      tokenFile: './test-token.json'
    };

    // Setup readline mock
    mockReadlineInterface = {
      question: vi.fn(),
      close: vi.fn()
    };
    (readline.createInterface as Mock).mockReturnValue(mockReadlineInterface);

    // Create service instance
    authService = new AuthenticationService(mockConfig, mockFileOps, mockLogger);
  });

  describe('constructor', () => {
    it('should initialize OAuth2Client with correct credentials', async () => {
      const { google } = await import('googleapis');
      expect(google.auth.OAuth2).toHaveBeenCalledWith(
        'test-client-id',
        'test-client-secret',
        'http://localhost:3000/callback'
      );
    });
  });

  describe('initialize', () => {
    it('should use saved tokens if available', async () => {
      const savedTokens = JSON.stringify(defaultTokens);
      (mockFileOps.readFile as Mock).mockReturnValue(savedTokens);

      const client = await authService.initialize();

      expect(mockFileOps.readFile).toHaveBeenCalledWith('./test-token.json');
      expect(mockOAuth2Client.setCredentials).toHaveBeenCalledWith(defaultTokens);
      expect(client).toBe(mockOAuth2Client);
      expect(mockLogger.log).not.toHaveBeenCalled(); // No OAuth flow needed
    });

    it('should perform OAuth flow if no saved tokens', async () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      mockOAuth2Client.generateAuthUrl.mockReturnValue('https://auth.url');
      mockOAuth2Client.getToken.mockResolvedValue({ tokens: defaultTokens });
      
      // Mock readline prompt
      mockReadlineInterface.question.mockImplementation((prompt: string, callback: Function) => {
        callback('test-auth-code');
      });

      const client = await authService.initialize();

      expect(mockLogger.log).toHaveBeenCalledWith(
        'Authorize this app by visiting this url: https://auth.url'
      );
      expect(mockOAuth2Client.getToken).toHaveBeenCalledWith('test-auth-code');
      expect(mockFileOps.writeFile).toHaveBeenCalledWith(
        './test-token.json',
        JSON.stringify(defaultTokens)
      );
      expect(client).toBe(mockOAuth2Client);
    });

    it('should handle invalid JSON in token file', async () => {
      (mockFileOps.readFile as Mock).mockReturnValue('invalid-json');
      mockOAuth2Client.generateAuthUrl.mockReturnValue('https://auth.url');
      mockOAuth2Client.getToken.mockResolvedValue({ tokens: defaultTokens });
      
      mockReadlineInterface.question.mockImplementation((prompt: string, callback: Function) => {
        callback('test-auth-code');
      });

      await authService.initialize();

      // Should perform OAuth flow since JSON parsing failed
      expect(mockLogger.log).toHaveBeenCalledWith(
        'Authorize this app by visiting this url: https://auth.url'
      );
    });
  });

  describe('getAuthUrl', () => {
    it('should generate auth URL with correct scopes', () => {
      mockOAuth2Client.generateAuthUrl.mockReturnValue('https://generated.auth.url');

      const url = authService.getAuthUrl();

      expect(mockOAuth2Client.generateAuthUrl).toHaveBeenCalledWith({
        access_type: 'offline',
        scope: [
          'https://www.googleapis.com/auth/youtube.upload',
          'https://www.googleapis.com/auth/spreadsheets.readonly',
          'https://www.googleapis.com/auth/drive.readonly'
        ]
      });
      expect(url).toBe('https://generated.auth.url');
    });
  });

  describe('getTokensFromCode', () => {
    it('should exchange code for tokens', async () => {
      mockOAuth2Client.getToken.mockResolvedValue({ 
        tokens: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token',
          scope: 'new-scope',
          token_type: 'Bearer',
          expiry_date: 9876543210
        }
      });

      const tokens = await authService.getTokensFromCode('auth-code-123');

      expect(mockOAuth2Client.getToken).toHaveBeenCalledWith('auth-code-123');
      expect(tokens).toEqual({
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        scope: 'new-scope',
        token_type: 'Bearer',
        expiry_date: 9876543210
      });
    });

    it('should handle missing optional token fields', async () => {
      mockOAuth2Client.getToken.mockResolvedValue({ 
        tokens: {
          access_token: 'minimal-token'
          // No other fields
        }
      });

      const tokens = await authService.getTokensFromCode('auth-code-456');

      expect(tokens).toEqual({
        access_token: 'minimal-token'
      });
    });

    it('should handle null token fields', async () => {
      mockOAuth2Client.getToken.mockResolvedValue({ 
        tokens: {
          access_token: 'token',
          refresh_token: null,
          scope: undefined,
          token_type: null,
          expiry_date: null
        }
      });

      const tokens = await authService.getTokensFromCode('auth-code-789');

      expect(tokens).toEqual({
        access_token: 'token'
      });
    });

    it('should throw on getToken failure', async () => {
      mockOAuth2Client.getToken.mockRejectedValue(new Error('Invalid code'));

      await expect(authService.getTokensFromCode('bad-code')).rejects.toThrow('Invalid code');
    });
  });

  describe('saveTokens', () => {
    it('should save tokens to file and set credentials', async () => {
      await authService.saveTokens(defaultTokens);

      expect(mockFileOps.writeFile).toHaveBeenCalledWith(
        './test-token.json',
        JSON.stringify(defaultTokens)
      );
      expect(mockOAuth2Client.setCredentials).toHaveBeenCalledWith(defaultTokens);
    });

    it('should use default token file if not specified in config', async () => {
      const configWithoutTokenFile: Config = {
        ...mockConfig,
        tokenFile: undefined
      };
      const service = new AuthenticationService(configWithoutTokenFile, mockFileOps, mockLogger);

      await service.saveTokens(defaultTokens);

      expect(mockFileOps.writeFile).toHaveBeenCalledWith(
        './token.json',
        JSON.stringify(defaultTokens)
      );
    });
  });

  describe('loadSavedTokens', () => {
    it('should load and parse saved tokens', async () => {
      const savedTokens = JSON.stringify(defaultTokens);
      (mockFileOps.readFile as Mock).mockReturnValue(savedTokens);

      const tokens = await authService.loadSavedTokens();

      expect(mockFileOps.readFile).toHaveBeenCalledWith('./test-token.json');
      expect(tokens).toEqual(defaultTokens);
    });

    it('should return null if file does not exist', async () => {
      (mockFileOps.readFile as Mock).mockReturnValue(null);

      const tokens = await authService.loadSavedTokens();

      expect(tokens).toBeNull();
    });

    it('should return null if JSON parsing fails', async () => {
      (mockFileOps.readFile as Mock).mockReturnValue('invalid-json{');

      const tokens = await authService.loadSavedTokens();

      expect(tokens).toBeNull();
    });

    it('should use default token file if not specified', async () => {
      const configWithoutTokenFile: Config = {
        ...mockConfig,
        tokenFile: undefined
      };
      const service = new AuthenticationService(configWithoutTokenFile, mockFileOps, mockLogger);

      await service.loadSavedTokens();

      expect(mockFileOps.readFile).toHaveBeenCalledWith('./token.json');
    });
  });

  describe('getAuthenticatedClient', () => {
    it('should return the OAuth2Client instance', () => {
      const client = authService.getAuthenticatedClient();

      expect(client).toBe(mockOAuth2Client);
    });
  });

  describe('OAuth flow integration', () => {
    it('should complete full OAuth flow', async () => {
      // Setup: no saved tokens
      (mockFileOps.readFile as Mock).mockReturnValue(null);
      
      // Mock auth URL generation
      mockOAuth2Client.generateAuthUrl.mockReturnValue('https://oauth.example.com');
      
      // Mock code exchange
      mockOAuth2Client.getToken.mockResolvedValue({ tokens: defaultTokens });
      
      // Mock user input
      mockReadlineInterface.question.mockImplementation((prompt: string, callback: Function) => {
        expect(prompt).toBe('Enter the code from that page here: ');
        callback('user-auth-code');
      });

      await authService.initialize();

      // Verify flow
      expect(mockLogger.log).toHaveBeenCalledWith(
        'Authorize this app by visiting this url: https://oauth.example.com'
      );
      expect(readline.createInterface).toHaveBeenCalledWith({
        input: process.stdin,
        output: process.stdout
      });
      expect(mockReadlineInterface.close).toHaveBeenCalled();
      expect(mockOAuth2Client.getToken).toHaveBeenCalledWith('user-auth-code');
      expect(mockFileOps.writeFile).toHaveBeenCalledWith(
        './test-token.json',
        JSON.stringify(defaultTokens)
      );
      expect(mockOAuth2Client.setCredentials).toHaveBeenCalledWith(defaultTokens);
    });
  });
});