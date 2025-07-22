# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube Bulk Upload tool - automates uploading multiple videos from Google Drive to YouTube using metadata from Google Sheets. The tool reads video metadata (Drive links, titles, descriptions, tags, unique IDs) from a Google Sheet and processes videos sequentially with progress tracking and resume capabilities. Implemented in both TypeScript and Python with identical functionality.

## Development Commands

### TypeScript (typescript/)

```bash
# Install dependencies
pnpm install

# Development commands (to be implemented)
pnpm run format      # prettier --write .
pnpm run lint        # eslint . --fix
pnpm run typecheck   # tsc --noEmit
pnpm run test        # vitest
pnpm run test:watch  # vitest --watch
pnpm run build       # tsc

# Run the script
pnpm start -- <spreadsheet_id>
```

### Python (python/)

```bash
# Install dependencies (to be implemented)
pip install -r requirements.txt  # or: pip install -e ".[dev]"

# Development commands (to be implemented)
make format      # black . && isort .
make lint        # mypy . && ruff check .
make test        # pytest
make test-watch  # pytest-watch
make all         # format, lint, test

# Run the script
python main.py <spreadsheet_id> [--sheet-range "Sheet1"] [--resume]
```

## Architecture

### Core Design Principles

1. **Pure Functions**: All business logic as pure functions with no side effects
2. **Dependency Injection**: I/O operations injected via interfaces/protocols
3. **Test-Driven Development**: Write tests first, especially for pure functions
4. **Integration Tests**: Mock all external dependencies (Google APIs, file system)

### Project Structure

- Both implementations follow identical architectural patterns
- Core logic separated from I/O operations
- Progress tracking allows resumable uploads
- Comprehensive error handling and logging
- Sequential batch processing of videos
- OAuth2 authentication flow for Google APIs

### Key Components

#### TypeScript Implementation (13KB)

- `YouTubeBulkUploader` class orchestrates the upload process
- Pure utility functions for data parsing and validation (exported for testing)
- FileOperations interface for dependency injection
- TypeScript interfaces for all data structures
- OAuth2 authentication flow implementation
- Progress management and comprehensive logging

#### Python Implementation (17KB)

- Main function with argument parsing
- FileOperations Protocol for dependency injection
- Dataclasses for type-safe data structures (`VideoData`, `FailedUpload`, `Config`)
- Type hints throughout the codebase
- Google API service builders
- Comprehensive error handling and retry logic

### Testing Strategy

1. **Unit Tests**: Test all pure functions in isolation
2. **Integration Tests**: Test main upload flow with mocked APIs
3. **Mock Requirements**:
   - Google Sheets API responses
   - Google Drive download operations
   - YouTube upload operations
   - File system operations

## Development Guidelines

1. Use unit test TDD of pure functions. NO side effects, NO I/O
2. Use integration tests for the main script. Mock ALL I/O
3. Regardless of language, use the best practices for that language and the best practices for software development in general. Correctness is more important than rapid development.
4. Use SOLID principles
5. Use KISS, YAGNI, DRY principles
6. Use standard developer tooling for each language
   1. TypeScript: tsc, vitest, eslint, prettier, with quality gates; format, type-check, lint, test, build
   2. Python: mypy, pytest, black, isort, with quality gates; format, type-check, lint, test, build
7. Dependencies and configuration and versions
   1. TypeScript: pnpm install. please use `pnpm outdated` regularly to check that you are using up to date tooling, and use internet searches to make sure you are using config and approaches suitable to latest version of each tool
   2. Python: pip install -r requirements.txt. please use `pip list` to check that you are using up to date tooling, and use internet searches to make sure you are using config and approaches suitable to latest version of each tool

## API Authentication

- Uses OAuth2 for Google APIs (Sheets, Drive, YouTube)
- Requires credentials.json for initial authentication
- Stores refresh tokens locally for subsequent runs
- Scopes required:
  - <https://www.googleapis.com/auth/spreadsheets.readonly>
  - <https://www.googleapis.com/auth/drive.readonly>
  - <https://www.googleapis.com/auth/youtube.upload>

## Common Development Tasks

### Adding New Features

1. Write unit tests for new pure functions first
2. Implement the pure function logic
3. Write integration tests for the feature
4. Update main orchestration if needed
5. Run full test suite before committing

### Debugging Upload Issues

- Check logs for detailed error messages
- Verify Google API quotas haven't been exceeded
- Ensure video files exist in Google Drive
- Validate spreadsheet data format
- Use --resume flag to continue from failures

## Current State and Improvement Areas

### Implemented Features

- OAuth2 authentication with token persistence
- Video metadata extraction from Google Sheets
- Video download from Google Drive
- YouTube upload with full metadata support
- Progress tracking and resume capability
- Comprehensive error handling and logging
- Retry logic for failed uploads

### Missing Components (Priority Order)

1. **Test Suite**: No unit or integration tests implemented
2. **Development Tooling**: Missing TypeScript config, Python project config
3. **Quality Tools**: No linting, formatting, or type-checking setup
4. **CI/CD Pipeline**: No automated quality gates
5. **Documentation**: Limited inline documentation

### Code Quality Improvements Needed

#### SOLID Principles Refactoring

- **SRP**: Extract services from main classes (Auth, Sheets, Drive, YouTube)
- **OCP**: Create interfaces/protocols for extensibility
- **DIP**: Depend on abstractions, not concrete implementations

#### Clean Code Practices

- **KISS**: Simplify complex functions and reduce cognitive complexity
- **YAGNI**: Remove any over-engineered solutions
- **DRY**: Extract common patterns and centralize configuration

## Data Structures

### Video Metadata Format (Spreadsheet)

- **Drive Link**: Google Drive URL to video file
- **Title**: YouTube video title
- **Description**: YouTube video description
- **Tags**: Comma-separated tags for YouTube
- **Unique ID**: Identifier for progress tracking

### Progress Tracking Structure

- **Processed IDs**: Set of successfully uploaded video IDs
- **Last Processed Row**: Resume point in spreadsheet
- **Failed Uploads**: Array with error details and timestamps
