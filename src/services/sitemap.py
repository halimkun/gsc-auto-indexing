"""
Async sitemap parser for GSC Auto Submit.

Fetches and parses sitemap.xml files, including nested/index sitemaps.

Author: halimkun (https://github.com/halimkun)
"""

import logging
from urllib.parse import urlparse

import aiohttp
from lxml import etree

logger = logging.getLogger(__name__)

# XML namespaces used in sitemaps
SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


async def fetch_sitemap(session: aiohttp.ClientSession, url: str) -> bytes | None:
    """Fetch sitemap XML content from a URL."""
    logger.info(f"Fetching sitemap: {url}")
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch sitemap {url}: HTTP {response.status}")
                return None
            content = await response.read()
            logger.info(f"Fetched sitemap: {url} ({len(content)} bytes)")
            return content
    except aiohttp.ClientError as e:
        logger.error(f"Network error fetching sitemap {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching sitemap {url}: {e}")
        return None


def parse_sitemap(xml_content: bytes) -> tuple[list[str], list[str]]:
    """
    Parse sitemap XML and return (page_urls, child_sitemap_urls).

    Handles both regular sitemaps (<urlset>) and sitemap indexes (<sitemapindex>).
    """
    page_urls: list[str] = []
    child_sitemaps: list[str] = []

    try:
        root = etree.fromstring(xml_content)
    except etree.XMLSyntaxError as e:
        logger.error(f"Failed to parse sitemap XML: {e}")
        return page_urls, child_sitemaps

    # Check for sitemap index (nested sitemaps)
    sitemap_entries = root.findall("sm:sitemap/sm:loc", namespaces=SITEMAP_NS)
    for loc in sitemap_entries:
        if loc.text:
            child_sitemaps.append(loc.text.strip())

    # Check for regular URL entries
    url_entries = root.findall("sm:url/sm:loc", namespaces=SITEMAP_NS)
    for loc in url_entries:
        if loc.text:
            page_urls.append(loc.text.strip())

    logger.info(f"Parsed sitemap: {len(page_urls)} URLs, {len(child_sitemaps)} child sitemaps")
    return page_urls, child_sitemaps


async def get_all_urls(base_url: str) -> list[str]:
    """
    Recursively fetch all page URLs from a sitemap, including nested sitemaps.

    Args:
        base_url: Domain (e.g. "example.com") or full URL to sitemap.xml
    """
    # Normalize input: if it's just a domain, build the sitemap URL
    if not base_url.startswith("http"):
        base_url = f"https://{base_url}"

    parsed = urlparse(base_url)
    if not parsed.path or parsed.path == "/":
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}/sitemap.xml"
    else:
        sitemap_url = base_url

    all_urls: list[str] = []
    visited_sitemaps: set[str] = set()
    queue: list[str] = [sitemap_url]

    async with aiohttp.ClientSession(
        headers={"User-Agent": "GSC-AutoSubmit/1.0"}
    ) as session:
        while queue:
            current_url = queue.pop(0)

            if current_url in visited_sitemaps:
                logger.debug(f"Skipping already visited sitemap: {current_url}")
                continue
            visited_sitemaps.add(current_url)

            xml_content = await fetch_sitemap(session, current_url)
            if xml_content is None:
                continue

            page_urls, child_sitemaps = parse_sitemap(xml_content)
            all_urls.extend(page_urls)

            for child in child_sitemaps:
                if child not in visited_sitemaps:
                    logger.info(f"Found child sitemap: {child}")
                    queue.append(child)

    logger.info(f"Total URLs collected from all sitemaps: {len(all_urls)}")
    return all_urls
