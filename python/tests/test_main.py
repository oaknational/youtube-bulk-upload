"""Tests for main entry point."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock

import pytest

from main import parse_arguments, build_config_from_args, cli
from models import Config


class TestMain:
    """Test main entry point functionality."""

    def test_parse_arguments_minimal(self):
        """Test parsing minimal arguments."""
        with patch.object(sys, 'argv', ['main.py', 'test_sheet_id']):
            args = parse_arguments()
            
        assert args.spreadsheet_id == 'test_sheet_id'
        assert args.sheet_range == 'Sheet1!A:E'
        assert args.resume is False
        assert args.retry_failed is False
        assert args.progress_file == 'progress.json'
        assert args.log_file == 'upload.log'

    def test_parse_arguments_full(self):
        """Test parsing all arguments."""
        with patch.object(sys, 'argv', [
            'main.py', 'test_sheet_id',
            '--sheet-range', 'Custom!B:F',
            '--resume',
            '--retry-failed',
            '--progress-file', 'custom_progress.json',
            '--log-file', 'custom.log',
            '--token-file', 'custom_token.json',
            '--temp-dir', '/tmp/custom',
            '--credentials-file', 'custom_creds.json'
        ]):
            args = parse_arguments()
            
        assert args.spreadsheet_id == 'test_sheet_id'
        assert args.sheet_range == 'Custom!B:F'
        assert args.resume is True
        assert args.retry_failed is True
        assert args.progress_file == 'custom_progress.json'
        assert args.log_file == 'custom.log'
        assert args.token_file == 'custom_token.json'
        assert args.temp_dir == '/tmp/custom'
        assert args.credentials_file == 'custom_creds.json'

    @patch('main.build_config_from_env')
    @patch('main.validate_required_config_fields')
    def test_build_config_from_args_success(self, mock_validate, mock_build_env):
        """Test successful config building."""
        # Mock environment config
        mock_build_env.return_value = {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'redirect_uri': 'http://localhost:8080'
        }
        mock_validate.return_value = []  # No errors
        
        # Create mock args
        args = Mock()
        args.spreadsheet_id = 'test_sheet'
        args.sheet_range = 'Sheet1!A:E'
        args.progress_file = 'progress.json'
        args.log_file = 'upload.log'
        args.token_file = 'token.json'
        args.temp_dir = './temp'
        args.credentials_file = 'creds.json'
        
        config = build_config_from_args(args)
        
        assert isinstance(config, Config)
        assert config.spreadsheet_id == 'test_sheet'
        assert config.client_id == 'test_client_id'

    @patch('main.build_config_from_env')
    def test_build_config_missing_credentials(self, mock_build_env):
        """Test config building with missing credentials."""
        mock_build_env.return_value = {}  # No credentials in env
        
        args = Mock()
        args.spreadsheet_id = 'test_sheet'
        args.credentials_file = 'nonexistent.json'
        
        # Mock Path.exists to return False
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(ValueError, match="Credentials file not found"):
                build_config_from_args(args)

    @patch('main.build_config_from_env')
    @patch('main.validate_required_config_fields')
    def test_build_config_validation_errors(self, mock_validate, mock_build_env):
        """Test config building with validation errors."""
        mock_build_env.return_value = {
            'client_id': 'test_id',
            'client_secret': 'test_secret',
            'redirect_uri': 'http://localhost'
        }
        mock_validate.return_value = ['Error 1', 'Error 2']
        
        args = Mock()
        args.spreadsheet_id = 'test_sheet'
        args.sheet_range = 'Sheet1!A:E'
        args.progress_file = 'progress.json'
        args.log_file = 'upload.log'
        args.token_file = 'token.json'
        args.temp_dir = './temp'
        
        with pytest.raises(ValueError, match="Missing required configuration fields"):
            build_config_from_args(args)

    @patch('main.asyncio.run')
    def test_cli(self, mock_asyncio_run):
        """Test CLI entry point."""
        cli()
        
        # Verify asyncio.run was called
        mock_asyncio_run.assert_called_once()
        # The argument should be a coroutine from calling main()
        assert mock_asyncio_run.call_args[0][0].__name__ == 'main'

    @patch('main.print_user_friendly_error')
    @patch('main.DependencyContainer')
    @patch('main.build_config_from_args')
    @patch('main.parse_arguments')
    @patch('main.print')
    async def test_main_success(
        self, mock_print, mock_parse, mock_build_config, mock_container, mock_error_print
    ):
        """Test successful main execution."""
        from main import main
        
        # Mock arguments
        mock_args = Mock()
        mock_args.resume = False
        mock_args.retry_failed = False
        mock_parse.return_value = mock_args
        
        # Mock config
        mock_config = Mock(spec=Config)
        mock_config.spreadsheet_id = 'test_sheet'
        mock_config.sheet_range = 'A:E'
        mock_config.progress_file = 'progress.json'
        mock_build_config.return_value = mock_config
        
        # Mock uploader
        mock_uploader = AsyncMock()
        mock_container_instance = Mock()
        mock_container_instance.create_youtube_bulk_uploader.return_value = mock_uploader
        mock_container.return_value = mock_container_instance
        
        # Mock os.path.exists to return False (no previous progress)
        with patch('main.os.path.exists', return_value=False):
            await main()
        
        # Verify calls
        mock_uploader.initialize.assert_called_once()
        mock_uploader.process_spreadsheet.assert_called_once()
        assert any("completed successfully" in str(call) for call in mock_print.call_args_list)

    # TODO: Fix this test - it hangs due to async/mock interaction
    # @patch('main.print')
    # @patch('main.sys.exit')
    # @patch('main.parse_arguments')
    # async def test_main_keyboard_interrupt(
    #     self, mock_parse, mock_exit, mock_print
    # ):
    #     """Test handling keyboard interrupt."""
    #     from main import main
    #     
    #     mock_parse.side_effect = KeyboardInterrupt()
    #     
    #     await main()
    #     
    #     mock_print.assert_called_with("\n\nProcess interrupted by user")
    #     mock_exit.assert_called_with(1)