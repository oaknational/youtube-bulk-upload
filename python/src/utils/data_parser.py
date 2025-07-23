"""Parse video data from spreadsheet rows."""

from typing import List, Optional

from models import VideoData


def parse_video_row(row: List[str]) -> Optional[VideoData]:
    """
    Parse a row of data from the spreadsheet into a structured VideoData object.

    Args:
        row: List of strings representing a spreadsheet row

    Returns:
        VideoData object if valid, None if invalid
    """
    # Validate row has enough columns
    if len(row) < 5:
        return None

    # Destructure the row
    drive_link = row[0].strip()
    title = row[1].strip()
    description = row[2].strip()
    tag_string = row[3].strip()
    unique_id = row[4].strip()

    # Check required fields (all except tags)
    if not drive_link or not title or not unique_id:
        return None

    # Parse tags - split by comma and trim each tag
    tags = [tag.strip() for tag in tag_string.split(",") if tag.strip()] if tag_string else []

    try:
        return VideoData(
            drive_link=drive_link,
            title=title,
            description=description,
            tags=tags,
            unique_id=unique_id,
        )
    except ValueError:
        # Handle validation errors from VideoData
        return None
