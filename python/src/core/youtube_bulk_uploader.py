"""Main orchestrator for bulk YouTube uploads."""

import asyncio
from typing import List

from interfaces import (
    IAuthenticationService,
    IGoogleSheetsService,
    ILogger,
    IProgressTracker,
)
from models import Config

from .spreadsheet_processor import process_video_rows
from .video_processor import VideoProcessor


class YouTubeBulkUploader:
    """Orchestrates the bulk upload process from spreadsheet to YouTube."""

    def __init__(
        self,
        auth_service: IAuthenticationService,
        sheets_service: IGoogleSheetsService,
        video_processor: VideoProcessor,
        progress_tracker: IProgressTracker,
        logger: ILogger,
        config: Config,
    ) -> None:
        """
        Initialize bulk uploader.

        Args:
            auth_service: Authentication service
            sheets_service: Google Sheets service
            video_processor: Video processor
            progress_tracker: Progress tracking service
            logger: Logger service
            config: Application configuration
        """
        self.auth_service = auth_service
        self.sheets_service = sheets_service
        self.video_processor = video_processor
        self.progress_tracker = progress_tracker
        self.logger = logger
        self.config = config

    async def initialize(self) -> None:
        """Initialize authentication."""
        self.auth_service.initialize()

    async def process_spreadsheet(self) -> None:
        """
        Process all videos from the configured spreadsheet.

        Raises:
            Exception: If fatal error occurs
        """
        try:
            # Fetch spreadsheet data
            rows = await self._fetch_spreadsheet_rows()

            if len(rows) == 0:
                self.logger.log("No data found in spreadsheet")
                return

            # Get current progress to determine start position
            progress = self.progress_tracker.get_progress()
            start_row = max(1, progress.last_processed_row)

            # Process videos
            await process_video_rows(
                rows=rows,
                start_row=start_row,
                logger=self.logger,
                progress_tracker=self.progress_tracker,
                video_processor=self.video_processor,
            )

            # Log final statistics
            self._log_final_stats()

        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Fatal error: {error_message}")
            raise

    async def retry_failed_uploads(self) -> None:
        """Retry all failed uploads by clearing them from processed list."""
        progress = self.progress_tracker.get_progress()
        failed_uploads = list(progress.failed_uploads)

        # Clear failed uploads list
        progress.failed_uploads = []
        self.progress_tracker.save_progress(progress)

        self.logger.log(f"Retrying {len(failed_uploads)} failed uploads...")

        # Remove failed videos from processed list so they can be retried
        for failed in failed_uploads:
            progress.processed_ids.discard(failed.unique_id)

        self.progress_tracker.save_progress(progress)

        # Re-process the spreadsheet - it will skip successful uploads and retry failed ones
        await self.process_spreadsheet()

    async def _fetch_spreadsheet_rows(self) -> List[List[str]]:
        """Fetch rows from configured spreadsheet."""
        return self.sheets_service.fetch_spreadsheet_data(
            self.config.spreadsheet_id,
            self.config.sheet_range
        )

    def _log_final_stats(self) -> None:
        """Log final upload statistics."""
        final_progress = self.progress_tracker.get_progress()
        self.logger.log("Upload process completed!")
        self.logger.log(f"Total processed: {len(final_progress.processed_ids)}")
        self.logger.log(f"Failed uploads: {len(final_progress.failed_uploads)}")