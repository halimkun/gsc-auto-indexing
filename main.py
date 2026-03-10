"""
GSC Auto Submit — CLI Entry Point

Auto-submit URLs from sitemap.xml to Google Search Console via Indexing API.

Author: halimkun (https://github.com/halimkun)
Repository: https://github.com/halimkun/gsc-auto-indexing
License: MIT

Usage:
    uv run python main.py <domain_or_url>
    uv run python main.py example.com
    uv run python main.py https://example.com/sitemap.xml
    uv run python main.py example.com --config /path/to/config.conf
    uv run python main.py example.com --db /path/to/submissions.csv
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from urllib.parse import urlparse

from rich.panel import Panel
from rich.table import Table

from src.core.config import get_service_account_path, load_config
from src.core.logger import console, setup_logger
from src.models.submission import SubmissionRecord
from src.services.database import get_existing_urls, load_records, save_or_update_record
from src.services.search_console import create_service, submit_url
from src.services.sitemap import get_all_urls

logger = logging.getLogger(__name__)

# Delay between API requests (seconds) to avoid rate limiting
SUBMIT_DELAY = 1.0


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="gsc",
        description="Auto-submit URLs from sitemap.xml to Google Search Console",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  uv run python main.py example.com\n"
            "  uv run python main.py https://example.com/sitemap.xml\n"
            "  uv run python main.py example.com --config ./config.conf\n"
            "  uv run python main.py example.com --db ./data/submissions.csv\n"
        ),
    )
    parser.add_argument(
        "domain",
        help="Domain or URL to fetch sitemap from (e.g. example.com or https://example.com/sitemap.xml)",
    )
    parser.add_argument(
        "--config",
        default="config.conf",
        help="Path to config file (default: config.conf)",
    )
    parser.add_argument(
        "--db",
        default="data/submissions.csv",
        help="Path to CSV database file (default: data/submissions.csv)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    return parser.parse_args()


def extract_domain(url_or_domain: str) -> str:
    """Extract clean domain from a URL or domain string."""
    if not url_or_domain.startswith("http"):
        url_or_domain = f"https://{url_or_domain}"
    parsed = urlparse(url_or_domain)
    return parsed.netloc or parsed.path


async def run(args: argparse.Namespace) -> None:
    """Main async execution flow."""
    domain = extract_domain(args.domain)

    # Header
    console.print()
    console.print(Panel.fit(
        f"[bold cyan]GSC Auto Submit[/bold cyan]\n"
        f"[dim]Domain:[/dim] [bold]{domain}[/bold]",
        border_style="cyan",
        subtitle="[dim]by @halimkun[/dim]",
        subtitle_align="right",
    ))
    console.print()

    # Step 1: Load config
    with console.status("[cyan]Loading configuration...", spinner="dots"):
        config = load_config(args.config)
        sa_path = get_service_account_path(config)
    console.print("  [green]✓[/green] Configuration loaded")

    # Step 2: Load existing records
    with console.status("[cyan]Loading database...", spinner="dots"):
        records = load_records(args.db)
        existing_urls = get_existing_urls(records)
    console.print(f"  [green]✓[/green] Database loaded — [dim]{len(records)} existing records[/dim]")

    # Step 3: Fetch all URLs from sitemap
    with console.status("[cyan]Fetching sitemap URLs...", spinner="dots"):
        all_urls = await get_all_urls(args.domain)

    if not all_urls:
        console.print("  [yellow]⚠[/yellow] No URLs found in sitemap. Exiting.")
        return

    console.print(f"  [green]✓[/green] Sitemap fetched — [bold]{len(all_urls)}[/bold] URLs found")

    # Step 4: Filter
    new_urls = [url for url in all_urls if url not in existing_urls]
    skipped = len(all_urls) - len(new_urls)

    if skipped > 0:
        console.print(f"  [dim]↳ {skipped} URLs already submitted (skipped)[/dim]")

    if not new_urls:
        console.print()
        console.print("  [green]✓ All URLs already submitted. Nothing to do![/green]")
        return

    console.print(f"  [cyan]→[/cyan] [bold]{len(new_urls)}[/bold] new URLs to submit")
    console.print()

    # Step 5: Connect to API
    with console.status("[cyan]Connecting to Google Indexing API...", spinner="dots"):
        service = create_service(sa_path)
    console.print("  [green]✓[/green] Connected to Google Indexing API")
    console.print()

    # Step 6: Submit URLs one by one
    success_count = 0
    fail_count = 0
    total = len(new_urls)

    for i, url in enumerate(new_urls, 1):
        success, message = await submit_url(service, url)
        now = datetime.now().isoformat()

        if success:
            status = "success"
            success_count += 1
            console.print(f"  [dim][{i}/{total}][/dim] [green]✓[/green] {url}")
        else:
            status = "failed"
            fail_count += 1
            console.print(f"  [dim][{i}/{total}][/dim] [red]✗[/red] {url} [dim]— {message}[/dim]")

        record = SubmissionRecord(
            domain=domain,
            url=url,
            status=status,
            created_at=now,
            updated_at=now,
        )
        save_or_update_record(args.db, record)

        # Delay between requests to avoid rate limiting
        if i < total:
            await asyncio.sleep(SUBMIT_DELAY)

    console.print()

    # Step 7: Summary table
    summary = Table(
        title="📊 Summary",
        show_header=False,
        border_style="dim",
        padding=(0, 2),
    )
    summary.add_column("Label", style="dim")
    summary.add_column("Value", style="bold")

    summary.add_row("Domain", f"[cyan]{domain}[/cyan]")
    summary.add_row("Total from sitemap", str(len(all_urls)))
    summary.add_row("Skipped (already done)", f"[dim]{skipped}[/dim]")
    summary.add_row("Submitted", str(len(new_urls)))
    summary.add_row("✓ Success", f"[green]{success_count}[/green]")
    summary.add_row("✗ Failed", f"[red]{fail_count}[/red]" if fail_count > 0 else f"[dim]{fail_count}[/dim]")

    console.print(summary)
    console.print()

    if fail_count > 0:
        console.print(
            f"  [yellow]⚠ {fail_count} URLs failed.[/yellow] "
            f"[dim]Re-run the command to retry.[/dim]"
        )
    else:
        console.print("  [bold green]🎉 All URLs submitted successfully![/bold green]")

    console.print("  [dim]github.com/halimkun/gsc[/dim]")
    console.print()


def main():
    """Entry point."""
    args = parse_args()

    # Setup logging (verbose shows internal logs, normal hides them)
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    setup_logger(level=log_level)

    try:
        asyncio.run(run(args))
    except FileNotFoundError as e:
        console.print(f"  [red]✗ Error:[/red] {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"  [red]✗ Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n  [yellow]Interrupted by user. Exiting.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"  [red]✗ Unexpected error:[/red] {e}")
        if args.verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
