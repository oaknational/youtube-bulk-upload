# YouTube Bulk Upload

A tool to bulk upload videos from Google Drive to YouTube using metadata from Google Sheets. The tool reads video information from a spreadsheet and automatically uploads videos with titles, descriptions, and tags.

## Features

- 📊 **Google Sheets Integration**: Read video metadata from spreadsheets
- 📁 **Google Drive Support**: Download videos directly from Drive
- 📹 **YouTube Upload**: Upload videos with full metadata
- 🔄 **Resume Capability**: Track progress and resume interrupted uploads
- 🚦 **Rate Limiting**: Automatic delays to respect API limits
- 📝 **Comprehensive Logging**: Detailed logs of all operations
- 🔐 **OAuth2 Authentication**: Secure Google API access

## Prerequisites

1. **Google Cloud Project** with the following APIs enabled:
   - YouTube Data API v3
   - Google Sheets API
   - Google Drive API

2. **OAuth2 Credentials**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth2 credentials (Desktop application type)
   - Download the credentials

3. **Google Sheet Format**:
   | Drive Link | Title | Description | Tags | Unique ID |
   |------------|-------|-------------|------|-----------|
   | https://drive.google.com/file/d/... | My Video | Video description | tag1,tag2 | video_001 |

## Installation

### TypeScript Version

```bash
cd typescript
pnpm install  # or npm install
```

### Python Version

```bash
cd python

# Create virtual environment (Python 3.8+)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development (includes testing and linting tools)
pip install -e ".[dev]"
```

## Configuration

### TypeScript

Set environment variables in `.env` file:

```env
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=http://localhost:3000/oauth2callback
SPREADSHEET_ID=your_spreadsheet_id  # Optional, can pass as argument
SHEET_RANGE=Sheet1!A:E  # Optional, defaults to Sheet1!A:E
TOKEN_FILE=./token.json  # Optional, defaults to ./token.json
LOG_FILE=./upload_log.txt  # Optional
PROGRESS_FILE=./upload_progress.json  # Optional
```

### Python

Create a `credentials.json` file with your OAuth2 credentials:

```json
{
  "installed": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uris": ["http://localhost:8080/"]
  }
}
```

## Usage

### TypeScript

```bash
# Development
pnpm run dev <spreadsheet_id>

# Production
pnpm run build
pnpm start <spreadsheet_id>

# With retry for failed uploads
pnpm start <spreadsheet_id> --retry-failed

# Run quality checks
pnpm run quality  # Runs format, lint, typecheck, and tests
```

### Python

```bash
# Basic usage
python main.py <spreadsheet_id>

# With custom sheet range
python main.py <spreadsheet_id> --sheet-range "Videos!A:E"

# Resume interrupted upload
python main.py <spreadsheet_id> --resume

# With custom credentials file
python main.py <spreadsheet_id> --credentials /path/to/credentials.json
```

## Development

### TypeScript Development

The TypeScript version follows SOLID principles with clean architecture:

```bash
# Run tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Check code quality
pnpm run lint:check
pnpm run format:check
pnpm run typecheck

# Fix issues
pnpm run lint
pnpm run format
```

### Project Structure

```
typescript/src/
├── core/           # Core business logic
├── interfaces/     # Service contracts (dependency inversion)
├── services/       # Service implementations
├── types/          # TypeScript type definitions
├── utils/          # Pure utility functions
└── main.ts         # Application entry point
```

## Authentication Flow

1. **First Run**: Opens browser for Google OAuth consent
2. **Token Storage**: Saves refresh token locally
3. **Subsequent Runs**: Uses saved token automatically
4. **Token Refresh**: Automatically refreshes expired tokens

## Progress Tracking

The tool saves progress after each successful upload:
- `upload_progress.json`: Tracks processed videos and last row
- Resume capability: Skip already uploaded videos
- Failed uploads: Logged with error details for retry

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Ensure OAuth2 credentials are correct
   - Check redirect URI matches configuration
   - Verify all required APIs are enabled

2. **API Quota Errors**:
   - YouTube API has daily quota limits
   - Use smaller batches if hitting limits
   - Check quota usage in Google Cloud Console

3. **Video Upload Failures**:
   - Verify video file exists in Google Drive
   - Check file permissions (must be readable)
   - Ensure video format is supported by YouTube

### Debug Mode

Set environment variable for verbose logging:
```bash
export DEBUG=youtube-bulk-upload
```

## API Scopes

The tool requires the following OAuth2 scopes:
- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/spreadsheets.readonly`
- `https://www.googleapis.com/auth/drive.readonly`

## Security

- OAuth tokens are stored locally (never commit them)
- Use `.gitignore` to exclude sensitive files
- Credentials are only used for API authentication
- All API calls use HTTPS

## Contributing

See [CLAUDE.md](./CLAUDE.md) for development guidelines and coding standards.

## License

[Add your license here]