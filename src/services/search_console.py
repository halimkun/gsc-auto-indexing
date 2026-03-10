"""
Google Search Console (Indexing API) client for GSC Auto Submit.

Uses the Google Indexing API to request URL indexing.
Includes automatic retry with exponential backoff for rate limiting.

Author: halimkun (https://github.com/halimkun)
"""

import asyncio
import logging

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/indexing"]
API_SERVICE_NAME = "indexing"
API_VERSION = "v3"

# Retry config
MAX_RETRIES = 3
BASE_DELAY = 2  # seconds


def create_service(service_account_path: str):
    """
    Create and return a Google Indexing API service client.

    Args:
        service_account_path: Path to the service account JSON key file.
    """
    logger.info("Creating Google Indexing API service client...")
    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES
        )
        service = build(API_SERVICE_NAME, API_VERSION, credentials=credentials)
        logger.info("Google Indexing API service client created successfully")
        return service
    except Exception as e:
        logger.error(f"Failed to create Google Indexing API service: {e}")
        raise


async def submit_url(service, url: str) -> tuple[bool, str]:
    """
    Submit a URL to Google for indexing using the Indexing API.
    Retries automatically on rate limit (429) with exponential backoff.

    Args:
        service: Google Indexing API service client.
        url: The URL to submit for indexing.

    Returns:
        Tuple of (success: bool, message: str)
    """
    body = {
        "url": url,
        "type": "URL_UPDATED",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = service.urlNotifications().publish(body=body).execute()
            notify_time = (
                response.get("urlNotificationMetadata", {})
                .get("latestUpdate", {})
                .get("notifyTime", "N/A")
            )
            return True, f"notifyTime: {notify_time}"

        except HttpError as e:
            status_code = e.resp.status

            # Rate limited — retry with backoff
            if status_code == 429 and attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))  # 2s, 4s, 8s
                logger.warning(f"Rate limited on {url}. Retrying in {delay}s... (attempt {attempt}/{MAX_RETRIES})")
                await asyncio.sleep(delay)
                continue

            return False, f"HTTP {status_code} — {e.reason}"

        except Exception as e:
            return False, str(e)

    return False, "Max retries exceeded"
