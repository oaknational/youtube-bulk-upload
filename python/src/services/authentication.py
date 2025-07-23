"""OAuth2 authentication service for Google APIs."""

import json
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from interfaces import IAuthenticationService, IFileOperations, ILogger
from models import AuthTokens, Config


class AuthenticationService(IAuthenticationService):
    """OAuth2 authentication implementation for Google APIs."""

    def __init__(
        self, config: Config, file_operations: IFileOperations, logger: ILogger
    ) -> None:
        """
        Initialize authentication service.

        Args:
            config: Application configuration
            file_operations: File operations service
            logger: Logger service
        """
        self.config = config
        self.file_operations = file_operations
        self.logger = logger
        self.credentials: Optional[Credentials] = None
        self.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]

    def initialize(self) -> Credentials:
        """
        Sets up authentication and returns OAuth2 credentials.

        Returns:
            Authenticated Google credentials

        Raises:
            Exception: If authentication fails
        """
        saved_tokens = self.load_saved_tokens()

        if saved_tokens and saved_tokens.refresh_token:
            self.credentials = Credentials(
                token=saved_tokens.access_token,
                refresh_token=saved_tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                scopes=self.scopes,
            )

            # Refresh token if expired
            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                self._save_credentials()
        else:
            # Perform OAuth2 flow
            self._perform_oauth_flow()

        if not self.credentials:
            raise Exception("Failed to initialize authentication")

        return self.credentials

    def get_auth_url(self) -> str:
        """
        Generates OAuth2 consent URL.

        Returns:
            Authorization URL for user consent
        """
        flow = self._create_flow()
        auth_url, _ = flow.authorization_url(prompt="consent")
        return auth_url

    def get_tokens_from_code(self, code: str) -> AuthTokens:
        """
        Exchanges auth code for tokens.

        Args:
            code: Authorization code from OAuth2 consent

        Returns:
            Authentication tokens
        """
        flow = self._create_flow()
        flow.fetch_token(code=code)

        credentials = flow.credentials
        return AuthTokens(
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            scope=credentials.scopes[0] if credentials.scopes else None,
            token_type="Bearer",
            expiry_date=int(credentials.expiry.timestamp() * 1000)
            if credentials.expiry
            else None,
        )

    def save_tokens(self, tokens: AuthTokens) -> None:
        """
        Persists tokens to storage.

        Args:
            tokens: Authentication tokens to save
        """
        token_data = tokens.to_dict()
        self.file_operations.write_file(self.config.token_file, json.dumps(token_data, indent=2))

    def load_saved_tokens(self) -> Optional[AuthTokens]:
        """
        Retrieves saved tokens.

        Returns:
            Saved authentication tokens or None if not found
        """
        if not self.file_operations.exists(self.config.token_file):
            return None

        try:
            content = self.file_operations.read_file(self.config.token_file)
            data = json.loads(content)
            return AuthTokens.from_dict(data)
        except Exception as e:
            self.logger.warn(f"Failed to load saved tokens: {e}")
            return None

    def get_authenticated_client(self) -> Credentials:
        """
        Returns authenticated OAuth2 credentials.

        Returns:
            Authenticated credentials

        Raises:
            Exception: If not authenticated
        """
        if not self.credentials:
            raise Exception("Not authenticated. Call initialize() first.")
        return self.credentials

    def _create_flow(self) -> Flow:
        """
        Create OAuth2 flow instance.

        Returns:
            Configured OAuth2 flow
        """
        client_config = {
            "web": {
                "client_id": self.config.client_id,
                "client_secret": self.config.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

        return Flow.from_client_config(
            client_config=client_config,
            scopes=self.scopes,
            redirect_uri=self.config.redirect_uri,
        )

    def _perform_oauth_flow(self) -> None:
        """
        Perform interactive OAuth2 flow.

        Raises:
            Exception: If authentication fails
        """
        try:
            auth_url = self.get_auth_url()
            self.logger.log(f"Authorize this app by visiting this url: {auth_url}")

            code = input("Enter the code from that page here: ")
            tokens = self.get_tokens_from_code(code)
            self.save_tokens(tokens)

            # Create credentials from tokens
            self.credentials = Credentials(
                token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                scopes=self.scopes,
            )
        except Exception:
            # Don't set credentials on failure
            pass

    def _save_credentials(self) -> None:
        """Save current credentials to token file."""
        if not self.credentials:
            return

        tokens = AuthTokens(
            access_token=self.credentials.token,
            refresh_token=self.credentials.refresh_token,
            scope=self.credentials.scopes[0] if self.credentials.scopes else None,
            token_type="Bearer",
            expiry_date=int(self.credentials.expiry.timestamp() * 1000)
            if self.credentials.expiry
            else None,
        )
        self.save_tokens(tokens)