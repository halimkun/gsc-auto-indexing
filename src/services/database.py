"""
CSV database handler for GSC Auto Submit.

Manages read/write operations on the CSV file used as a simple database.

Author: halimkun (https://github.com/halimkun)
"""

import csv
import logging
import os
from pathlib import Path

from src.models.submission import SubmissionRecord

logger = logging.getLogger(__name__)


def ensure_db_exists(db_path: str) -> None:
    """Create the CSV file with headers if it doesn't exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists():
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(SubmissionRecord.csv_headers())
        logger.info(f"Created new database file: {db_path}")
    else:
        logger.info(f"Database file exists: {db_path}")


def load_records(db_path: str) -> list[SubmissionRecord]:
    """Load all submission records from CSV."""
    ensure_db_exists(db_path)
    records: list[SubmissionRecord] = []

    with open(db_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        for row in reader:
            if len(row) >= 5:
                try:
                    records.append(SubmissionRecord.from_row(row))
                except Exception as e:
                    logger.warning(f"Skipping malformed row: {row} — {e}")

    logger.info(f"Loaded {len(records)} records from database")
    return records


def _rewrite_all(db_path: str, records: list[SubmissionRecord]) -> None:
    """Rewrite the entire CSV file with the given records."""
    with open(db_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SubmissionRecord.csv_headers())
        for r in records:
            writer.writerow(r.to_row())


def save_or_update_record(db_path: str, record: SubmissionRecord) -> None:
    """
    Upsert a record: update if URL already exists, otherwise append.

    When updating, only status and updated_at are changed.
    """
    ensure_db_exists(db_path)
    records = load_records(db_path)

    # Check if URL already exists
    for existing in records:
        if existing.url == record.url:
            logger.debug(f"Updating existing record: {record.url} [{existing.status} -> {record.status}]")
            existing.status = record.status
            existing.updated_at = record.updated_at
            _rewrite_all(db_path, records)
            return

    # New URL — append
    with open(db_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(record.to_row())

    logger.debug(f"Saved new record: {record.url} [{record.status}]")


def url_exists(records: list[SubmissionRecord], url: str) -> bool:
    """Check if a URL already exists in the records (with success status)."""
    return any(r.url == url and r.status == "success" for r in records)


def get_existing_urls(records: list[SubmissionRecord]) -> set[str]:
    """Get a set of all successfully submitted URLs for fast lookup."""
    urls = {r.url for r in records if r.status == "success"}
    logger.info(f"Found {len(urls)} previously successful URLs in database")
    return urls
