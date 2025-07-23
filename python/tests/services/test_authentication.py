"""Tests for AuthenticationService."""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest
from google.oauth2.credentials import Credentials

from interfaces import IFileOperations, ILogger
from models import AuthTokens, Config
from services.authentication import AuthenticationService


class TestAuthenticationService:
    """Test AuthenticationService."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8080",
            spreadsheet_id="test_spreadsheet",
        )

    @pytest.fixture
    def mock_file_ops(self):
        """Create mock file operations."""
        mock = Mock(spec=IFileOperations)
        # Default: token file doesn't exist
        mock.exists.return_value = False
        return mock

    @pytest.fixture
    def mock_logger(self):
        """Create mock logger."""
        return Mock(spec=ILogger)

    @pytest.fixture
    def auth_service(self, config, mock_file_ops, mock_logger):
        """Create AuthenticationService instance."""
        return AuthenticationService(config, mock_file_ops, mock_logger)

    @pytest.fixture
    def sample_tokens(self):
        """Create sample auth tokens."""
        return AuthTokens(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            scope="https://www.googleapis.com/auth/youtube.upload",
            token_type="Bearer",
            expiry_date=int((datetime.now() + timedelta(hours=1)).timestamp() * 1000),
        )

    def test_load_saved_tokens_file_not_exists(self, auth_service, mock_file_ops):
        """Test loading tokens when file doesn't exist."""
        mock_file_ops.exists.return_value = False
        
        result = auth_service.load_saved_tokens()
        
        assert result is None
        mock_file_ops.read_file.assert_not_called()

    def test_load_saved_tokens_success(self, auth_service, mock_file_ops, sample_tokens):
        """Test successfully loading saved tokens."""
        mock_file_ops.exists.return_value = True
        mock_file_ops.read_file.return_value = json.dumps(sample_tokens.to_dict())
        
        result = auth_service.load_saved_tokens()
        
        assert result is not None
        assert result.access_token == sample_tokens.access_token
        assert result.refresh_token == sample_tokens.refresh_token

    def test_load_saved_tokens_invalid_json(self, auth_service, mock_file_ops, mock_logger):
        """Test loading tokens with invalid JSON."""
        mock_file_ops.exists.return_value = True
        mock_file_ops.read_file.return_value = "invalid json{"
        
        result = auth_service.load_saved_tokens()
        
        assert result is None
        mock_logger.warn.assert_called_once()

    def test_save_tokens(self, auth_service, mock_file_ops, sample_tokens, config):
        """Test saving tokens to file."""
        auth_service.save_tokens(sample_tokens)
        
        mock_file_ops.write_file.assert_called_once()
        file_path, content = mock_file_ops.write_file.call_args[0]
        assert file_path == config.token_file
        
        # Verify saved content
        saved_data = json.loads(content)
        assert saved_data["access_token"] == sample_tokens.access_token
        assert saved_data["refresh_token"] == sample_tokens.refresh_token

    @patch("services.authentication.Flow")
    def test_get_auth_url(self, mock_flow_class, auth_service):
        """Test generating auth URL."""
        mock_flow = Mock()
        mock_flow.authorization_url.return_value = ("https://auth.url", "state")
        mock_flow_class.from_client_config.return_value = mock_flow
        
        url = auth_service.get_auth_url()
        
        assert url == "https://auth.url"
        mock_flow.authorization_url.assert_called_once_with(prompt="consent")

    @patch("services.authentication.Flow")
    def test_get_tokens_from_code(self, mock_flow_class, auth_service):
        """Test exchanging auth code for tokens."""
        # Create mock credentials
        mock_credentials = Mock()
        mock_credentials.token = "new_access_token"
        mock_credentials.refresh_token = "new_refresh_token"
        mock_credentials.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        mock_credentials.expiry = datetime.now() + timedelta(hours=1)
        
        # Create mock flow
        mock_flow = Mock()
        mock_flow.credentials = mock_credentials
        mock_flow_class.from_client_config.return_value = mock_flow
        
        tokens = auth_service.get_tokens_from_code("auth_code_123")
        
        assert tokens.access_token == "new_access_token"
        assert tokens.refresh_token == "new_refresh_token"
        mock_flow.fetch_token.assert_called_once_with(code="auth_code_123")

    def test_get_authenticated_client_not_initialized(self, auth_service):
        """Test getting client before initialization."""
        with pytest.raises(Exception, match="Not authenticated"):
            auth_service.get_authenticated_client()

    @patch("services.authentication.Credentials")
    def test_initialize_with_saved_tokens(
        self, mock_credentials_class, auth_service, mock_file_ops, sample_tokens
    ):
        """Test initialization with existing saved tokens."""
        # Setup saved tokens
        mock_file_ops.exists.return_value = True
        mock_file_ops.read_file.return_value = json.dumps(sample_tokens.to_dict())
        
        # Create mock credentials
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.expired = False
        mock_credentials.refresh_token = sample_tokens.refresh_token
        mock_credentials_class.return_value = mock_credentials
        
        result = auth_service.initialize()
        
        assert result == mock_credentials
        assert auth_service.credentials == mock_credentials
        mock_credentials.refresh.assert_not_called()

    @patch("services.authentication.Request")
    @patch("services.authentication.Credentials")
    def test_initialize_with_expired_tokens(
        self, mock_credentials_class, mock_request_class, auth_service, mock_file_ops, sample_tokens
    ):
        """Test initialization with expired tokens that need refresh."""
        # Setup saved tokens
        mock_file_ops.exists.return_value = True
        mock_file_ops.read_file.return_value = json.dumps(sample_tokens.to_dict())
        
        # Create mock credentials
        mock_credentials = Mock(spec=Credentials)
        mock_credentials.expired = True
        mock_credentials.refresh_token = sample_tokens.refresh_token
        mock_credentials.token = "refreshed_token"
        mock_credentials.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        mock_credentials.expiry = datetime.now() + timedelta(hours=1)
        mock_credentials_class.return_value = mock_credentials
        
        # Create mock request
        mock_request = Mock()
        mock_request_class.return_value = mock_request
        
        result = auth_service.initialize()
        
        assert result == mock_credentials
        mock_credentials.refresh.assert_called_once_with(mock_request)
        # Should save refreshed credentials
        mock_file_ops.write_file.assert_called()

    @patch("builtins.input", return_value="auth_code_123")
    @patch("services.authentication.Flow")
    @patch("services.authentication.Credentials")
    def test_initialize_without_saved_tokens(
        self, mock_credentials_class, mock_flow_class, mock_input,
        auth_service, mock_file_ops, mock_logger
    ):
        """Test initialization without saved tokens (full OAuth flow)."""
        # No saved tokens
        mock_file_ops.exists.return_value = False
        
        # Setup mock flow
        mock_flow = Mock()
        mock_flow.authorization_url.return_value = ("https://auth.url", "state")
        mock_credentials_from_flow = Mock()
        mock_credentials_from_flow.token = "new_access_token"
        mock_credentials_from_flow.refresh_token = "new_refresh_token"
        mock_credentials_from_flow.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        mock_credentials_from_flow.expiry = datetime.now() + timedelta(hours=1)
        mock_flow.credentials = mock_credentials_from_flow
        mock_flow_class.from_client_config.return_value = mock_flow
        
        # Setup mock credentials
        mock_credentials = Mock(spec=Credentials)
        mock_credentials_class.return_value = mock_credentials
        
        result = auth_service.initialize()
        
        assert result == mock_credentials
        # Should log auth URL
        mock_logger.log.assert_called()
        assert "https://auth.url" in mock_logger.log.call_args[0][0]
        # Should save new tokens
        mock_file_ops.write_file.assert_called()

    @patch("services.authentication.Flow")
    def test_flow_configuration(self, mock_flow_class, auth_service, config):
        """Test OAuth2 flow configuration."""
        # Mock the flow creation
        mock_flow = Mock()
        mock_flow_class.from_client_config.return_value = mock_flow
        
        # Call the method
        flow = auth_service._create_flow()
        
        # Verify Flow.from_client_config was called with correct params
        mock_flow_class.from_client_config.assert_called_once()
        call_args = mock_flow_class.from_client_config.call_args
        
        # Check client config
        client_config = call_args[1]["client_config"]
        assert client_config["web"]["client_id"] == config.client_id
        assert client_config["web"]["client_secret"] == config.client_secret
        
        # Check scopes
        assert call_args[1]["scopes"] == auth_service.scopes
        
        # Check redirect URI
        assert call_args[1]["redirect_uri"] == config.redirect_uri

    def test_save_credentials(self, auth_service, mock_file_ops):
        """Test saving current credentials."""
        # Setup mock credentials
        mock_creds = Mock()
        mock_creds.token = "current_token"
        mock_creds.refresh_token = "current_refresh"
        mock_creds.scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        mock_creds.expiry = datetime.now() + timedelta(hours=1)
        auth_service.credentials = mock_creds
        
        auth_service._save_credentials()
        
        mock_file_ops.write_file.assert_called_once()
        _, content = mock_file_ops.write_file.call_args[0]
        saved_data = json.loads(content)
        assert saved_data["access_token"] == "current_token"
        assert saved_data["refresh_token"] == "current_refresh"

    def test_save_credentials_no_credentials(self, auth_service, mock_file_ops):
        """Test saving credentials when none exist."""
        auth_service.credentials = None
        auth_service._save_credentials()
        
        mock_file_ops.write_file.assert_not_called()

    def test_scopes_configuration(self, auth_service):
        """Test that all required scopes are configured."""
        expected_scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly",
        ]
        assert auth_service.scopes == expected_scopes

    def test_implements_protocol(self, config, mock_file_ops, mock_logger):
        """Test that AuthenticationService implements IAuthenticationService protocol."""
        from interfaces import IAuthenticationService
        
        auth_service = AuthenticationService(config, mock_file_ops, mock_logger)
        # This would fail at runtime if protocol not satisfied
        _: IAuthenticationService = auth_service

    @patch("builtins.input", side_effect=Exception("OAuth failed"))
    @patch("services.authentication.Flow")
    def test_initialize_failure(self, mock_flow_class, mock_input, auth_service, mock_file_ops):
        """Test initialization failure raises exception."""
        # No saved tokens
        mock_file_ops.exists.return_value = False
        
        # Setup mock flow
        mock_flow = Mock()
        mock_flow.authorization_url.return_value = ("https://auth.url", "state")
        mock_flow_class.from_client_config.return_value = mock_flow
        
        with pytest.raises(Exception, match="Failed to initialize authentication"):
            auth_service.initialize()