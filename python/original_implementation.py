#!/usr/bin/env python3
"""
YouTube Bulk Upload Script
Uploads videos from Google Sheets to YouTube with resume capabilities
"""

import os
import json
import logging
import pickle
import re
import time
import tempfile
import argparse
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple, Any, Protocol
from dataclasses import dataclass, asdict
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import httplib2

# Type definitions
@dataclass
class VideoData:
    """Data structure for video metadata"""
    drive_link: str
    title: str
    description: str
    tags: List[str]
    unique_id: str

@dataclass
class FailedUpload:
    """Data structure for failed upload attempts"""
    unique_id: str
    error: str
    timestamp: str

@dataclass
class Config:
    """Configuration for the uploader"""
    credentials_file: str
    token_file: str = 'token.pickle'
    progress_file: str = 'upload_progress.json'
    log_file: str = 'upload_log.txt'
    temp_dir: Optional[str] = None

# Protocol for file operations (for dependency injection)
class FileOperations(Protocol):
    def read_file(self, path: str, mode: str = 'r') -> Optional[Any]: ...
    def write_file(self, path: str, content: Any, mode: str = 'w') -> None: ...
    def exists(self, path: str) -> bool: ...
    def remove(self, path: str) -> None: ...
    def makedirs(self, path: str, exist_ok: bool = True) -> None: ...

# Default file operations implementation
class DefaultFileOperations:
    def read_file(self, path: str, mode: str = 'r') -> Optional[Any]:
        try:
            with open(path, mode) as f:
                if mode == 'rb':
                    return pickle.load(f)
                elif mode == 'r':
                    return f.read()
        except FileNotFoundError:
            return None
        except Exception:
            return None
    
    def write_file(self, path: str, content: Any, mode: str = 'w') -> None:
        with open(path, mode) as f:
            if mode == 'wb':
                pickle.dump(content, f)
            elif mode == 'w':
                f.write(content if isinstance(content, str) else json.dumps(content, indent=2))
    
    def exists(self, path: str) -> bool:
        return os.path.exists(path)
    
    def remove(self, path: str) -> None:
        os.remove(path)
    
    def makedirs(self, path: str, exist_ok: bool = True) -> None:
        os.makedirs(path, exist_ok=exist_ok)

# Pure utility functions
def extract_file_id_from_drive_link(link: str) -> Optional[str]:
    """Extract file ID from various Google Drive URL formats"""
    patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
        r'/open\?id=([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)
    
    return None

def parse_video_row(row: List[str]) -> Optional[VideoData]:
    """Parse a spreadsheet row into VideoData"""
    if len(row) < 5:
        return None
    
    return VideoData(
        drive_link=row[0],
        title=row[1],
        description=row[2],
        tags=[tag.strip() for tag in row[3].split(',')] if row[3] else [],
        unique_id=row[4]
    )

def serialize_progress(processed_ids: Set[str], last_row: int, failed: List[FailedUpload]) -> str:
    """Serialize progress data to JSON string"""
    return json.dumps({
        'processed_ids': list(processed_ids),
        'last_processed_row': last_row,
        'failed_uploads': [asdict(fu) for fu in failed]
    }, indent=2)

def deserialize_progress(data: str) -> Tuple[Set[str], int, List[FailedUpload]]:
    """Deserialize JSON string to progress data"""
    try:
        parsed = json.loads(data)
        processed_ids = set(parsed.get('processed_ids', []))
        last_row = parsed.get('last_processed_row', 0)
        failed = [FailedUpload(**fu) for fu in parsed.get('failed_uploads', [])]
        return processed_ids, last_row, failed
    except Exception:
        return set(), 0, []

def create_log_message(message: str) -> str:
    """Create a formatted log message with timestamp"""
    return f"[{datetime.now().isoformat()}] {message}"

# Progress management functions
def load_progress(progress_file: str, file_ops: FileOperations) -> Tuple[Set[str], int, List[FailedUpload]]:
    """Load progress from file"""
    content = file_ops.read_file(progress_file)
    if content:
        return deserialize_progress(content)
    return set(), 0, []

def save_progress(
    progress_file: str,
    processed_ids: Set[str],
    last_row: int,
    failed: List[FailedUpload],
    file_ops: FileOperations
) -> None:
    """Save progress to file"""
    content = serialize_progress(processed_ids, last_row, failed)
    file_ops.write_file(progress_file, content)

# Authentication functions
def load_credentials(token_file: str, file_ops: FileOperations) -> Optional[Credentials]:
    """Load saved credentials from file"""
    return file_ops.read_file(token_file, 'rb')

def save_credentials(token_file: str, creds: Credentials, file_ops: FileOperations) -> None:
    """Save credentials to file"""
    file_ops.write_file(token_file, creds, 'wb')

def authenticate_with_oauth(
    credentials_file: str,
    scopes: List[str],
    port: int = 0
) -> Credentials:
    """Perform OAuth authentication flow"""
    flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
    return flow.run_local_server(port=port)

def refresh_credentials(creds: Credentials) -> Credentials:
    """Refresh expired credentials"""
    creds.refresh(Request())
    return creds

# Google API operations
def build_services(creds: Credentials) -> Dict[str, Any]:
    """Build Google API service objects"""
    return {
        'youtube': build('youtube', 'v3', credentials=creds),
        'sheets': build('sheets', 'v4', credentials=creds),
        'drive': build('drive', 'v3', credentials=creds)
    }

def download_file_from_drive(
    drive_service: Any,
    file_id: str,
    output_path: str
) -> bool:
    """Download a file from Google Drive"""
    try:
        request = drive_service.files().get_media(fileId=file_id)
        
        with open(output_path, 'wb') as f:
            downloader = MediaFileUpload(output_path, resumable=True)
            done = False
            
            while not done:
                _, done = downloader.next_chunk()
        
        return True
    except HttpError:
        return False

def upload_video_to_youtube(
    youtube_service: Any,
    video_path: str,
    video_data: VideoData,
    max_retries: int = 5
) -> Optional[str]:
    """Upload video to YouTube with retry logic"""
    body = {
        'snippet': {
            'title': video_data.title,
            'description': video_data.description,
            'tags': video_data.tags,
            'categoryId': '22'  # People & Blogs
        },
        'status': {
            'privacyStatus': 'private',
            'selfDeclaredMadeForKids': False
        }
    }
    
    insert_request = youtube_service.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=MediaFileUpload(
            video_path,
            chunksize=-1,
            resumable=True
        )
    )
    
    response = None
    retry = 0
    
    while response is None and retry <= max_retries:
        try:
            status, response = insert_request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"\rUploading: {progress}%", end='')
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                retry += 1
                time.sleep(2 ** retry)
            else:
                return None
        except Exception:
            return None
    
    print()  # New line after progress
    
    if response:
        return response.get('id')
    return None

def fetch_spreadsheet_data(
    sheets_service: Any,
    spreadsheet_id: str,
    range_name: str
) -> List[List[str]]:
    """Fetch data from Google Sheets"""
    try:
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        return result.get('values', [])
    except HttpError:
        return []

# Main processing function
def process_single_video(
    video_data: VideoData,
    services: Dict[str, Any],
    temp_dir: str,
    file_ops: FileOperations,
    logger: Optional[logging.Logger] = None
) -> str:
    """Process a single video: download and upload"""
    # Extract file ID
    file_id = extract_file_id_from_drive_link(video_data.drive_link)
    if not file_id:
        raise ValueError("Invalid Google Drive link")
    
    # Ensure temp directory exists
    file_ops.makedirs(temp_dir)
    
    # Download video
    temp_video_path = os.path.join(temp_dir, f"{video_data.unique_id}.mp4")
    
    if not download_file_from_drive(services['drive'], file_id, temp_video_path):
        raise Exception("Failed to download video from Drive")
    
    if logger:
        logger.info(f"Downloaded video: {temp_video_path}")
    
    try:
        # Upload to YouTube
        youtube_id = upload_video_to_youtube(
            services['youtube'],
            temp_video_path,
            video_data
        )
        
        if not youtube_id:
            raise Exception("Failed to upload video to YouTube")
        
        return youtube_id
    finally:
        # Clean up temp file
        file_ops.remove(temp_video_path)

# Main uploader class using pure functions
class YouTubeBulkUploader:
    """Main class for bulk uploading videos to YouTube"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/spreadsheets.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]
    
    def __init__(
        self,
        config: Config,
        file_ops: FileOperations = None,
        logger: logging.Logger = None
    ):
        self.config = config
        self.file_ops = file_ops or DefaultFileOperations()
        self.logger = logger or self._setup_logger()
        self.services = None
        
    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(self.config.log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger
    
    def authenticate(self) -> None:
        """Authenticate and build Google API services"""
        creds = load_credentials(self.config.token_file, self.file_ops)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds = refresh_credentials(creds)
            else:
                creds = authenticate_with_oauth(
                    self.config.credentials_file,
                    self.SCOPES
                )
            
            save_credentials(self.config.token_file, creds, self.file_ops)
        
        self.services = build_services(creds)
        self.logger.info("Authentication successful")
    
    def process_videos(self, spreadsheet_id: str, range_name: str = 'Sheet1!A:E') -> None:
        """Process all videos from the spreadsheet"""
        if not self.services:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        # Load progress
        processed_ids, last_row, failed_uploads = load_progress(
            self.config.progress_file,
            self.file_ops
        )
        
        # Fetch spreadsheet data
        rows = fetch_spreadsheet_data(
            self.services['sheets'],
            spreadsheet_id,
            range_name
        )
        
        if not rows:
            self.logger.error("No data found in spreadsheet")
            return
        
        # Determine temp directory
        temp_dir = self.config.temp_dir or tempfile.mkdtemp(prefix='youtube_upload_')
        
        # Process videos
        start_row = max(1, last_row)
        
        for i in range(start_row, len(rows)):
            video_data = parse_video_row(rows[i])
            
            if not video_data:
                self.logger.warning(f"Row {i+1} has insufficient data, skipping")
                continue
            
            if video_data.unique_id in processed_ids:
                self.logger.info(f"Skipping already processed video: {video_data.unique_id}")
                continue
            
            self.logger.info(f"Processing video {i+1}/{len(rows)}: {video_data.unique_id}")
            
            try:
                youtube_id = process_single_video(
                    video_data,
                    self.services,
                    temp_dir,
                    self.file_ops,
                    self.logger
                )
                
                self.logger.info(f"Successfully uploaded: {video_data.unique_id} -> {youtube_id}")
                
                # Update progress
                processed_ids.add(video_data.unique_id)
                last_row = i + 1
                save_progress(
                    self.config.progress_file,
                    processed_ids,
                    last_row,
                    failed_uploads,
                    self.file_ops
                )
                
            except Exception as e:
                self.logger.error(f"Failed to process {video_data.unique_id}: {e}")
                failed_uploads.append(
                    FailedUpload(
                        unique_id=video_data.unique_id,
                        error=str(e),
                        timestamp=datetime.now().isoformat()
                    )
                )
                save_progress(
                    self.config.progress_file,
                    processed_ids,
                    last_row,
                    failed_uploads,
                    self.file_ops
                )
            
            # Rate limiting
            time.sleep(2)
        
        # Clean up temp directory if we created it
        if not self.config.temp_dir and self.file_ops.exists(temp_dir):
            try:
                os.rmdir(temp_dir)
            except:
                pass
        
        self.logger.info("Upload process completed!")
        self.logger.info(f"Total processed: {len(processed_ids)}")
        self.logger.info(f"Failed uploads: {len(failed_uploads)}")
    
    def retry_failed_uploads(self) -> None:
        """Retry failed uploads"""
        processed_ids, last_row, failed_uploads = load_progress(
            self.config.progress_file,
            self.file_ops
        )
        
        failed_to_retry = list(failed_uploads)
        failed_uploads.clear()
        
        self.logger.info(f"Retrying {len(failed_to_retry)} failed uploads...")
        
        for failed in failed_to_retry:
            processed_ids.discard(failed.unique_id)
        
        save_progress(
            self.config.progress_file,
            processed_ids,
            last_row,
            failed_uploads,
            self.file_ops
        )

def main(args: Optional[List[str]] = None) -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Bulk upload videos to YouTube')
    parser.add_argument('spreadsheet_id', help='Google Sheets spreadsheet ID')
    parser.add_argument('--range', default='Sheet1!A:E', help='Sheet range (default: Sheet1!A:E)')
    parser.add_argument('--credentials', default='credentials.json', help='Path to credentials file')
    parser.add_argument('--retry-failed', action='store_true', help='Retry failed uploads')
    
    parsed_args = parser.parse_args(args)
    
    config = Config(credentials_file=parsed_args.credentials)
    uploader = YouTubeBulkUploader(config)
    
    try:
        uploader.authenticate()
        
        if parsed_args.retry_failed:
            uploader.retry_failed_uploads()
        
        uploader.process_videos(parsed_args.spreadsheet_id, parsed_args.range)
        
    except KeyboardInterrupt:
        uploader.logger.info("Upload interrupted by user")
    except Exception as e:
        uploader.logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main()