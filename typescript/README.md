# YouTube Bulk Upload - TypeScript Implementation

A modern TypeScript implementation of the YouTube bulk upload tool, built with clean architecture
principles and comprehensive tooling.

## 🏗️ Architecture

This implementation follows SOLID principles with a clean architecture approach:

### Core Components

- **DependencyContainer**: IoC container for dependency injection
- **VideoProcessor**: Orchestrates the video processing workflow
- **YouTubeBulkUploader**: Main application orchestrator

### Services (with Interfaces)

1. **AuthenticationService**: OAuth2 authentication flow
2. **GoogleSheetsService**: Spreadsheet data operations
3. **GoogleDriveService**: Video file downloads
4. **YouTubeService**: YouTube upload operations
5. **ProgressTracker**: Progress persistence and tracking
6. **Logger**: Logging with consola v3
7. **FileOperations**: File system operations

### Utilities

Pure functions for data parsing, validation, and serialization.

## 🚀 Quick Start

```bash
# Install dependencies
pnpm install

# Set up environment variables
cp .env.example .env  # Edit with your credentials

# Run in development
pnpm run dev <spreadsheet_id>

# Build and run in production
pnpm run build
pnpm start <spreadsheet_id>
```

## 📋 Environment Configuration

Create a `.env` file with:

```env
# Required
CLIENT_ID=your_google_client_id
CLIENT_SECRET=your_google_client_secret
REDIRECT_URI=http://localhost:3000/oauth2callback

# Optional
SPREADSHEET_ID=default_spreadsheet_id
SHEET_RANGE=Sheet1!A:E
TOKEN_FILE=./token.json
PROGRESS_FILE=./upload_progress.json
LOG_FILE=./upload_log.txt
TEMP_DIR=./temp
```

## 🧪 Development

### Available Scripts

```bash
# Quality checks
pnpm run quality      # Run all checks (format, lint, typecheck, test)
pnpm run format       # Format code with Prettier
pnpm run lint         # Lint with ESLint
pnpm run typecheck    # Type check with TypeScript
pnpm test            # Run tests

# Development
pnpm run dev         # Run with tsx (hot reload)
pnpm test:watch      # Run tests in watch mode

# Build
pnpm run build       # Compile TypeScript
pnpm run clean       # Clean build artifacts
```

### Project Structure

```
src/
├── core/
│   ├── DependencyContainer.ts
│   ├── VideoProcessor.ts
│   ├── YouTubeBulkUploader.ts
│   └── spreadsheetProcessor.ts
├── interfaces/
│   ├── IAuthenticationService.ts
│   ├── IGoogleSheetsService.ts
│   ├── IGoogleDriveService.ts
│   ├── IYouTubeService.ts
│   ├── IProgressTracker.ts
│   ├── ILogger.ts
│   └── IFileOperations.ts
├── services/
│   ├── AuthenticationService.ts
│   ├── GoogleSheetsService.ts
│   ├── GoogleDriveService.ts
│   ├── YouTubeService.ts
│   ├── ProgressTracker.ts
│   ├── Logger.ts
│   └── FileOperations.ts
├── types/
│   └── index.ts
├── utils/
│   ├── configBuilder.ts
│   ├── configValidator.ts
│   ├── dataParser.ts
│   ├── driveUtils.ts
│   ├── errorPrinter.ts
│   ├── logging.ts
│   └── progressSerializer.ts
└── main.ts
```

## 🧰 Technology Stack

- **TypeScript 5.7**: Strict mode with full type safety
- **Node.js 18+**: ESM modules only
- **pnpm**: Fast, efficient package manager
- **Vitest 3**: Modern testing framework
- **ESLint 9**: Code quality with flat config
- **Prettier 3**: Code formatting
- **tsx**: TypeScript execution for development
- **consola 3**: Beautiful console logging

## 📊 Google Sheets Format

Your spreadsheet should have these columns:

| Column | Description | Example                             |
| ------ | ----------- | ----------------------------------- |
| A      | Drive Link  | https://drive.google.com/file/d/... |
| B      | Title       | My Amazing Video                    |
| C      | Description | This video shows...                 |
| D      | Tags        | tutorial,programming,typescript     |
| E      | Unique ID   | video_001                           |

## 🔄 Progress Tracking

The tool automatically tracks progress:

- Saves after each successful upload
- Skips already processed videos
- Logs failed uploads with error details
- Supports `--retry-failed` flag to retry failures

## 🧪 Testing

```bash
# Run all tests
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run with coverage
pnpm test:coverage
```

Current test coverage:

- ✅ Pure utility functions (16 tests)
- 🚧 Service unit tests (coming soon)
- 🚧 Integration tests (coming soon)

## 🐛 Debugging

Enable debug logging:

```bash
# Via environment variable
export DEBUG=youtube-bulk-upload
pnpm start <spreadsheet_id>

# Or in .env file
DEBUG=youtube-bulk-upload
```

## 🔒 Security

- OAuth tokens stored locally in `token.json`
- Never commit tokens or credentials
- All sensitive files in `.gitignore`
- Environment variables for configuration
- HTTPS for all API calls

## 📝 Code Quality

All code passes strict quality gates:

- ✅ **TypeScript**: Strict mode, no `any` types
- ✅ **ESLint**: No errors or warnings
- ✅ **Prettier**: Consistent formatting
- ✅ **Tests**: All tests passing

## 🤝 Contributing

1. Follow the guidelines in [CLAUDE.md](../CLAUDE.md)
2. Use TDD for new features
3. Ensure all quality gates pass
4. Write pure functions where possible
5. Add appropriate tests

## 📄 License

[Your license here]
