# YouTube Bulk Upload - Python Implementation

A Python implementation of the YouTube bulk upload tool, built with clean architecture principles, comprehensive testing, and modern Python best practices.

## 🐍 Python Environment Setup

This project uses Python's built-in `venv` module for environment management - the most canonical and widely understood approach in the Python ecosystem.

### Prerequisites

- Python 3.8 or higher
- pip (comes with Python)

### Setting Up Your Environment

```bash
# 1. Navigate to the Python directory
cd python

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
# For production use:
pip install -r requirements.txt

# For development (includes testing and linting tools):
pip install -e ".[dev]"

# 5. Verify installation
python -c "import src; print('✓ Installation successful')"
```

### Deactivating the Environment

When you're done working:
```bash
deactivate
```

### Why Virtual Environments?

- **Isolation**: Project dependencies don't affect system Python
- **Reproducibility**: Exact versions specified in requirements.txt
- **Clean**: Easy to delete and recreate if needed
- **Standard**: Works everywhere Python runs

## 🏗️ Architecture

This implementation mirrors the TypeScript version with Python idioms:

### Core Components

- **DependencyContainer**: IoC container for dependency injection
- **VideoProcessor**: Orchestrates single video processing
- **YouTubeBulkUploader**: Main application orchestrator

### Services (with Protocols)

1. **FileOperations** → `IFileOperations`
2. **Logger** → `ILogger`
3. **ProgressTracker** → `IProgressTracker`
4. **AuthenticationService** → `IAuthenticationService`
5. **GoogleSheetsService** → `IGoogleSheetsService`
6. **GoogleDriveService** → `IGoogleDriveService`
7. **YouTubeService** → `IYouTubeService`

### Pure Utility Functions

- `extract_file_id_from_drive_link`
- `parse_video_row`
- `validate_config`
- `build_config_from_args`
- `process_video_rows`

## 🚀 Quick Start

```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Set up Google OAuth credentials
# Download credentials.json from Google Cloud Console and place in project root

# Run the tool
python -m src.main SPREADSHEET_ID

# With options
python -m src.main SPREADSHEET_ID --sheet-range "Videos!A:E" --resume

# Retry failed uploads
python -m src.main SPREADSHEET_ID --retry-failed
```

## 📋 Configuration

### OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth2 credentials (Desktop application type)
3. Download as `credentials.json`
4. Place in the project root directory

The credentials.json should look like:
```json
{
  "installed": {
    "client_id": "your_client_id.apps.googleusercontent.com",
    "client_secret": "your_client_secret",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "redirect_uris": ["http://localhost"]
  }
}
```

### File Locations

- `token.pickle`: Stored OAuth tokens (created after first auth)
- `upload_progress.json`: Upload progress tracking
- `upload_log.txt`: Detailed operation logs
- `temp_videos/`: Temporary video storage during processing

## 🧪 Development

### Available Commands

All development tasks are managed through the Makefile:

```bash
# Install development dependencies
make dev-install

# Code formatting
make format         # Auto-format with black and isort
make format-check   # Check formatting without changes

# Linting and type checking
make lint          # Run ruff linter
make typecheck     # Run mypy type checker

# Testing
make test          # Run all tests
make test-unit     # Run unit tests only
make test-integration  # Run integration tests only
make test-watch    # Run tests in watch mode
make coverage      # Generate coverage report

# Quality gates (run all checks)
make quality       # Must pass before committing

# Run everything
make all          # Format, lint, typecheck, and test
```

### Project Structure

```
python/
├── src/
│   ├── __init__.py
│   ├── core/                  # Core business logic
│   │   ├── dependency_container.py
│   │   ├── video_processor.py
│   │   ├── youtube_bulk_uploader.py
│   │   └── spreadsheet_processor.py
│   ├── interfaces/            # Protocol definitions
│   │   └── protocols.py
│   ├── services/              # Service implementations
│   │   ├── authentication_service.py
│   │   ├── file_operations.py
│   │   ├── google_drive_service.py
│   │   ├── google_sheets_service.py
│   │   ├── logger.py
│   │   ├── progress_tracker.py
│   │   └── youtube_service.py
│   ├── types/                 # Data models
│   │   └── models.py
│   ├── utils/                 # Pure utility functions
│   │   ├── config_builder.py
│   │   ├── config_validator.py
│   │   ├── data_parser.py
│   │   ├── drive_utils.py
│   │   └── error_printer.py
│   └── main.py               # Entry point
├── tests/
│   ├── fixtures/             # Test data and mocks
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
├── Makefile                  # Development commands
├── pyproject.toml           # Python project configuration
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── setup.py                 # Package configuration
└── README.md               # This file
```

## 🧰 Technology Stack

- **Python 3.8+**: Modern Python with full type hints
- **Type Hints**: 100% typed with Protocol interfaces
- **MyPy**: Strict mode type checking
- **Pytest**: Testing framework with fixtures
- **Black**: Code formatting (opinionated)
- **isort**: Import sorting
- **Ruff**: Fast Python linter
- **Coverage.py**: Code coverage reporting

## 📊 Google Sheets Format

Your spreadsheet should have these columns:

| Column | Description | Example |
|--------|-------------|---------|
| A | Drive Link | https://drive.google.com/file/d/abc123/view |
| B | Title | My Amazing Video |
| C | Description | This video demonstrates... |
| D | Tags | tutorial,python,programming |
| E | Unique ID | video_001 |

## 🧪 Testing

The project includes comprehensive tests matching the TypeScript implementation:

```bash
# Run all tests
make test

# Run with coverage
make coverage

# Run specific test file
pytest tests/unit/test_specific.py -v

# Run tests matching pattern
pytest -k "test_video_processor" -v
```

### Test Categories

- **Unit Tests**: Pure functions and isolated services
- **Integration Tests**: Full workflow testing with mocks
- **Fixtures**: Reusable test data and mock objects

## 🔄 Progress Tracking

The tool automatically tracks progress:

- Saves after each successful upload
- Skips already processed videos on resume
- Tracks failed uploads with error details
- Supports retry of failed uploads

Progress file structure:
```json
{
  "processed_ids": ["video_001", "video_002"],
  "last_processed_row": 3,
  "failed_uploads": [
    {
      "unique_id": "video_003",
      "error": "Network timeout",
      "timestamp": "2024-12-23T10:30:00"
    }
  ]
}
```

## 🐛 Debugging

### Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG
python -m src.main SPREADSHEET_ID

# Or use Python's logging
export PYTHONVERBOSE=1
```

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -e .` for development

2. **Authentication Errors**
   - Check credentials.json exists
   - Delete token.pickle to re-authenticate
   - Verify API scopes are enabled

3. **Type Errors**
   - Run `make typecheck` to catch issues
   - Ensure all functions have type hints

## 🔒 Security

- OAuth tokens stored in `token.pickle` (gitignored)
- Never commit `credentials.json` or tokens
- All sensitive files excluded via `.gitignore`
- Uses Google's official auth libraries
- HTTPS for all API communications

## 📝 Code Quality Standards

All code must pass these quality gates:

- ✅ **Black**: Code formatting (line length 100)
- ✅ **isort**: Import organization
- ✅ **MyPy**: Strict type checking (no Any types)
- ✅ **Ruff**: No linting errors
- ✅ **Pytest**: All tests passing
- ✅ **Coverage**: >80% code coverage

## 🤝 Contributing

1. Always work in a virtual environment
2. Run `make quality` before committing
3. Write tests for new features (TDD preferred)
4. Follow existing patterns and architecture
5. Update documentation as needed

### Development Workflow

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Make changes
# ... edit files ...

# 3. Run quality checks
make quality

# 4. Commit if all passes
git add .
git commit -m "feat: add new feature"
```

## 📦 Distribution

To package for distribution:

```bash
# Build distribution packages
python setup.py sdist bdist_wheel

# Install from package
pip install dist/youtube_bulk_upload-1.0.0.tar.gz
```

## 📄 License

[Your license here]