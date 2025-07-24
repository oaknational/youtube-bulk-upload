"""Spreadsheet processing logic for bulk video uploads."""

import asyncio
from typing import List

from interfaces import ILogger, IProgressTracker
from utils.data_parser import parse_video_row

from .video_processor import VideoProcessor


async def process_video_rows(
    rows: List[List[str]],
    start_row: int,
    logger: ILogger,
    progress_tracker: IProgressTracker,
    video_processor: VideoProcessor,
) -> None:
    """
    Process video rows from spreadsheet sequentially.

    Args:
        rows: Spreadsheet rows containing video data
        start_row: Row index to start processing from (0-based)
        logger: Logger for output
        progress_tracker: Progress tracking service
        video_processor: Video processing service
    """
    for i in range(start_row, len(rows)):
        row = rows[i]

        # Skip empty rows
        if not row:
            logger.log(f"Row {i + 1} is empty, skipping")
            continue

        # Parse video data from row
        try:
            video_data = parse_video_row(row)
            if not video_data:
                logger.log(f"Row {i + 1} has invalid data, skipping")
                continue
        except Exception:
            logger.log(f"Row {i + 1} has invalid data, skipping")
            continue

        # Skip already processed videos
        if progress_tracker.is_video_processed(video_data.unique_id):
            logger.log(f"Skipping already processed video: {video_data.unique_id}")
            continue

        # Process the video
        logger.log(f"Processing video {i + 1}/{len(rows)}: {video_data.unique_id}")

        try:
            youtube_id = video_processor.process_video(video_data)
            
            logger.log(
                f"Successfully uploaded: {video_data.unique_id} -> YouTube ID: {youtube_id}"
            )
            
            progress_tracker.mark_video_processed(video_data.unique_id)
            progress_tracker.update_last_processed_row(i + 1)
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to process {video_data.unique_id}: {error_message}")
            progress_tracker.mark_video_failed(video_data.unique_id, error_message)

        # Rate limiting delay (2 seconds between videos)
        await asyncio.sleep(2)