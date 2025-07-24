"""Main entry point for YouTube Bulk Upload tool."""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from core import DependencyContainer
from models import Config
from utils.config_builder import build_config_from_env
from utils.config_validator import validate_required_config_fields
from utils.error_printer import print_user_friendly_error


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Upload videos from Google Drive to YouTube using metadata from Google Sheets"
    )
    
    parser.add_argument(
        "spreadsheet_id",
        help="Google Sheets spreadsheet ID containing video metadata"
    )
    
    parser.add_argument(
        "--sheet-range",
        default="Sheet1!A:E",
        help="Range in the spreadsheet to read (default: Sheet1!A:E)"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous progress"
    )
    
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Retry previously failed uploads"
    )
    
    parser.add_argument(
        "--progress-file",
        default="progress.json",
        help="Progress tracking file (default: progress.json)"
    )
    
    parser.add_argument(
        "--log-file",
        default="upload.log",
        help="Log file path (default: upload.log)"
    )
    
    parser.add_argument(
        "--token-file",
        default="token.json",
        help="OAuth token file path (default: token.json)"
    )
    
    parser.add_argument(
        "--temp-dir",
        default="./temp_videos",
        help="Temporary directory for downloaded videos (default: ./temp_videos)"
    )
    
    parser.add_argument(
        "--credentials-file",
        default="credentials.json",
        help="Path to OAuth2 credentials file (default: credentials.json)"
    )
    
    return parser.parse_args()


def build_config_from_args(args: argparse.Namespace) -> Config:
    """
    Build configuration from command-line arguments and environment.

    Args:
        args: Parsed command-line arguments

    Returns:
        Configuration object

    Raises:
        ValueError: If configuration is invalid
    """
    # Start with environment variables
    config_dict = build_config_from_env()
    
    # Override with command-line arguments
    config_dict.update({
        "spreadsheet_id": args.spreadsheet_id,
        "sheet_range": args.sheet_range,
        "progress_file": args.progress_file,
        "log_file": args.log_file,
        "token_file": args.token_file,
        "temp_dir": args.temp_dir,
    })
    
    # Load credentials from file if not in environment
    if not config_dict.get("client_id") or not config_dict.get("client_secret"):
        credentials_path = Path(args.credentials_file)
        if not credentials_path.exists():
            raise ValueError(
                f"Credentials file not found: {args.credentials_file}\n"
                "Please download credentials.json from Google Cloud Console"
            )
        
        # For simplicity, we'll require these to be set as environment variables
        # In a real implementation, you'd parse the credentials.json file
        raise ValueError(
            "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables"
        )
    
    # Create and validate config
    config = Config(**config_dict)
    missing_fields = validate_required_config_fields(config)
    
    if missing_fields:
        error_msg = "Missing required configuration fields:\n" + "\n".join(f"- {field}" for field in missing_fields)
        raise ValueError(error_msg)
    
    return config


async def main() -> None:
    """Main application entry point."""
    args = parse_arguments()
    
    try:
        # Build configuration
        config = build_config_from_args(args)
        
        # Create dependency container
        container = DependencyContainer(config)
        
        # Create uploader
        uploader = container.create_youtube_bulk_uploader()
        
        # Initialize (authenticate)
        print("Initializing authentication...")
        await uploader.initialize()
        
        # Handle different modes
        if args.retry_failed:
            print("Retrying failed uploads...")
            await uploader.retry_failed_uploads()
        else:
            # Clear progress if not resuming
            if not args.resume and os.path.exists(config.progress_file):
                print(f"Clearing previous progress from {config.progress_file}")
                os.remove(config.progress_file)
            
            print(f"Processing spreadsheet: {config.spreadsheet_id}")
            print(f"Range: {config.sheet_range}")
            await uploader.process_spreadsheet()
        
        print("\nUpload process completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_user_friendly_error(e)
        sys.exit(1)


def cli() -> None:
    """CLI entry point for setuptools."""
    asyncio.run(main())


if __name__ == "__main__":
    cli()