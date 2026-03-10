"""
Data models for GSC Auto Submit.

Author: halimkun (https://github.com/halimkun)
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SubmissionRecord:
    """Represents a single URL submission record in the CSV database."""

    domain: str
    url: str
    status: str  # "success" | "failed" | "skipped"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @staticmethod
    def csv_headers() -> list[str]:
        """Return CSV column headers."""
        return ["domain", "url", "status", "created_at", "updated_at"]

    def to_row(self) -> list[str]:
        """Convert record to a CSV row."""
        return [self.domain, self.url, self.status, self.created_at, self.updated_at]

    @classmethod
    def from_row(cls, row: list[str]) -> "SubmissionRecord":
        """Create a SubmissionRecord from a CSV row."""
        return cls(
            domain=row[0],
            url=row[1],
            status=row[2],
            created_at=row[3],
            updated_at=row[4],
        )
