# GSC Auto Submit

> Auto-submit URLs from `sitemap.xml` to Google Search Console via the [Google Indexing API](https://developers.google.com/search/apis/indexing-api/v3/quickstart).

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## ✨ Features

- 🔍 Fetches URLs from `sitemap.xml` (supports nested/index sitemaps)
- 🚀 Submits URLs to Google Indexing API for indexing
- 📊 CSV-based database to track submissions and avoid duplicates
- 🔄 Failed URLs can be retried by re-running the command
- ⚡ Full async I/O for sitemap fetching
- 🎨 Beautiful colored terminal output with [Rich](https://github.com/Textualize/rich)
- 🛡️ Auto-retry with exponential backoff on rate limiting
- 📝 Detailed logging (verbose mode available)

## 📋 Prerequisites

1. **Python 3.10+** and **[uv](https://docs.astral.sh/uv/)** package manager
2. **Google Cloud Project** with the [Web Search Indexing API](https://console.cloud.google.com/apis/library/indexing.googleapis.com) enabled
3. **Service Account** with a JSON key file ([create one here](https://console.cloud.google.com/iam-admin/serviceaccounts))
4. Add the Service Account email as **Owner** in [Google Search Console](https://search.google.com/search-console) → Settings → Users and permissions

## 🚀 Setup

```bash
# Clone the repository
git clone https://github.com/halimkun/gsc-auto-indexing.git
cd gsc

# Install dependencies
uv sync

# Copy and edit config
cp config.conf.example config.conf
# Edit config.conf and set the path to your service account JSON file
```

## 📖 Usage

```bash
# Submit all URLs from a domain's sitemap
uv run python main.py example.com

# Submit from a specific sitemap URL
uv run python main.py https://example.com/sitemap-articles.xml

# Use custom config and database paths
uv run python main.py example.com --config /path/to/config.conf --db /path/to/db.csv

# Enable verbose logging
uv run python main.py example.com -v
```

### Example Output

```
╭─────────────────────────────────────╮
│ GSC Auto Submit                     │
│ Domain: example.com                 │
╰───────────────────── by @halimkun ─╯

  ✓ Configuration loaded
  ✓ Database loaded — 0 existing records
  ✓ Sitemap fetched — 22 URLs found
  → 22 new URLs to submit
  ✓ Connected to Google Indexing API

  [1/22] ✓ https://example.com/page-1
  [2/22] ✓ https://example.com/page-2
  [3/22] ✗ https://example.com/page-3 — HTTP 403 — Permission denied
  ...

  📊 Summary
  Domain              example.com
  Total from sitemap  22
  Skipped             0
  Submitted           22
  ✓ Success           21
  ✗ Failed            1

  ⚠ 1 URLs failed. Re-run the command to retry.
  github.com/halimkun/gsc
```

## 📁 Project Structure

```
gsc/
├── main.py                     # Entry point + CLI
├── pyproject.toml              # Dependencies & metadata
├── config.conf.example         # Config template
├── LICENSE                     # MIT License
├── data/
│   └── submissions.csv         # CSV database (auto-created)
└── src/
    ├── core/
    │   ├── config.py           # Config loader
    │   └── logger.py           # Rich logging setup
    ├── models/
    │   └── submission.py       # SubmissionRecord dataclass
    └── services/
        ├── database.py         # CSV database handler (upsert)
        ├── sitemap.py          # Async sitemap parser
        └── search_console.py   # Google Indexing API client
```

## ⚙️ How It Works

1. Parse the domain/URL argument
2. Load Google credentials from `config.conf`
3. Load existing submission records from CSV database
4. Fetch all URLs from `sitemap.xml` (recursively follows nested sitemaps)
5. Filter out URLs already successfully submitted
6. Submit new URLs to Google Indexing API (with 1s delay between requests)
7. Save results to CSV database (upsert — updates existing, appends new)
8. Display summary with colored output

## ⚠️ Important Notes

- **Google Indexing API Quota:** 200 requests per day by default. The tool includes auto-retry with exponential backoff for rate limiting.
- **Service Account as Owner:** The Service Account must be added as **Owner** (not just user) in Google Search Console for the Indexing API to work.
- **URL Types:** The Indexing API officially supports `JobPosting` and `BroadcastEvent` schema types, but is widely used for all URL types by SEO tools.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

## 👤 Author

**halimkun** — [github.com/halimkun](https://github.com/halimkun)
