# AI Code Assistant Instructions — GSC Auto Submit

> Gunakan instruksi ini sebagai referensi utama saat menghasilkan atau memodifikasi kode di project ini.

---

## 📌 Project Overview

**GSC Auto Submit** adalah CLI tool berbasis Python untuk auto-submit URL dari `sitemap.xml` ke Google Search Console menggunakan [Google Indexing API v3](https://developers.google.com/search/apis/indexing-api/v3/quickstart).

- **Author:** halimkun
- **License:** MIT
- **Python:** ≥ 3.10
- **Package manager:** [uv](https://docs.astral.sh/uv/)
- **Entry point:** `main.py` → fungsi `main()`
- **CLI runner:** `uv run python main.py <domain_or_url>`

---

## 🏗️ Arsitektur & Struktur Project

```
gsc-auto-indexing/
├── main.py                          # CLI entry point + orchestrator (argparse)
├── pyproject.toml                   # Dependencies & project metadata (uv/pip)
├── config.conf.example              # Template konfigurasi (configparser format)
├── .gitignore
├── data/
│   └── submissions.csv              # CSV database (auto-created at runtime)
└── src/
    ├── __init__.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py                # Config loader (configparser)
    │   └── logger.py                # Rich console + logging setup
    ├── models/
    │   ├── __init__.py
    │   └── submission.py            # SubmissionRecord dataclass
    └── services/
        ├── __init__.py
        ├── database.py              # CSV read/write/upsert operations
        ├── search_console.py        # Google Indexing API client
        └── sitemap.py               # Async sitemap parser (aiohttp + lxml)
```

### Layer Architecture

| Layer        | Folder           | Tanggung Jawab                                      |
|--------------|------------------|------------------------------------------------------|
| **Entry**    | `main.py`        | CLI parsing, orchestration flow, Rich UI output      |
| **Core**     | `src/core/`      | Config management, logging & console setup           |
| **Models**   | `src/models/`    | Data structures / dataclasses                        |
| **Services** | `src/services/`  | Business logic: API client, database, sitemap parser |

---

## 📦 Dependencies

| Package                       | Kegunaan                              |
|-------------------------------|---------------------------------------|
| `aiohttp` (≥3.9.0)           | Async HTTP client (fetch sitemap)     |
| `google-api-python-client` (≥2.100.0) | Google API client library      |
| `google-auth` (≥2.23.0)      | Google OAuth2 / Service Account auth  |
| `lxml` (≥5.0.0)              | XML parsing (sitemap)                 |
| `rich` (≥13.0.0)             | Colored terminal output & logging     |

> **Jangan** menambahkan `requests` — gunakan `aiohttp` untuk semua HTTP calls.  
> **Jangan** menambahkan `click` atau `typer` — CLI menggunakan `argparse` bawaan Python.

---

## 🧑‍💻 Coding Conventions

### General Rules

1. **Python 3.10+ features:** Gunakan modern type hints (`list[str]`, `str | None`, `tuple[bool, str]`). Jangan gunakan `from __future__ import annotations` kecuali benar-benar diperlukan.
2. **Type annotations wajib** pada semua function signatures (parameter dan return type).
3. **Docstrings wajib** pada setiap module, class, dan function publik. Format: triple-quoted string dengan deskripsi singkat, lalu `Args:` / `Returns:` jika diperlukan.
4. **Module-level docstring** di setiap file, mengandung: deskripsi modul, author credit.
5. **Gunakan `logging`** (bukan `print`) untuk log internal. Setiap modul harus membuat logger sendiri:
   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```
6. **Gunakan `console` dari `src.core.logger`** untuk output yang ditampilkan ke user (Rich markup). Jangan gunakan `print()` langsung.
7. **Async by default:** Fungsi yang melakukan I/O (network, file besar) harus `async`. Gunakan `asyncio` untuk concurrency.
8. **Constants** didefinisikan di module level, UPPER_SNAKE_CASE.
9. **Import style:**
   - Standard library → Third-party → Local (`src.xxx`)
   - Satu import per line untuk local modules
   - Gunakan absolute imports: `from src.core.config import load_config`

### Naming Conventions

| Jenis           | Convention         | Contoh                        |
|-----------------|--------------------|-------------------------------|
| Module          | `snake_case`       | `search_console.py`          |
| Function        | `snake_case`       | `get_all_urls()`             |
| Class           | `PascalCase`       | `SubmissionRecord`           |
| Constant        | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `BASE_DELAY`  |
| Private func    | `_snake_case`      | `_rewrite_all()`             |
| Variable        | `snake_case`       | `all_urls`, `success_count`  |

### Error Handling Pattern

- Raise **specific exceptions** (`FileNotFoundError`, `ValueError`) — jangan raise generic `Exception`.
- Catch exceptions di level service, log via `logger.error()`, lalu re-raise atau return error tuple.
- `main.py` adalah top-level exception boundary yang menampilkan error ke user via Rich console.
- Untuk API calls, gunakan **retry with exponential backoff** (lihat pattern di `search_console.py`).

```python
# Pattern: Return tuple (success, message) untuk operasi yang bisa gagal
async def submit_url(service, url: str) -> tuple[bool, str]:
    try:
        # ... logic
        return True, "OK"
    except HttpError as e:
        return False, f"HTTP {e.resp.status} — {e.reason}"
```

### Data Models

- Gunakan `@dataclass` untuk data structures.
- Sertakan method `to_row()`, `from_row()`, dan `csv_headers()` jika model disimpan ke CSV.
- Default values via `field(default_factory=...)`.

```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class SubmissionRecord:
    domain: str
    url: str
    status: str  # "success" | "failed" | "skipped"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
```

---

## 🎨 Terminal Output (Rich)

- **Semua output UI** menggunakan `console` dari `src.core.logger` (instance `rich.Console` dengan custom theme).
- Gunakan **Rich markup** untuk styling: `[green]✓[/green]`, `[red]✗[/red]`, `[dim]...[/dim]`, `[bold cyan]...[/bold cyan]`.
- Gunakan `console.status()` untuk spinner saat operasi berlangsung.
- Gunakan `rich.table.Table` untuk summary / data tabular.
- Gunakan `rich.panel.Panel` untuk header/branding.

### Custom Theme Colors

```python
# Defined in src/core/logger.py
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "dim": "dim white",
    "highlight": "bold magenta",
    "url": "underline blue",
})
```

### Output Icons

| Status   | Icon | Contoh                          |
|----------|------|---------------------------------|
| Success  | `✓`  | `[green]✓[/green] Done`        |
| Failed   | `✗`  | `[red]✗[/red] Failed`          |
| Warning  | `⚠`  | `[yellow]⚠[/yellow] Warning`   |
| Arrow    | `→`  | `[cyan]→[/cyan] Processing`    |
| Counter  | `[i/n]` | `[dim][1/22][/dim]`          |

---

## 🔑 Configuration

- Gunakan `configparser` (INI format) — **bukan** YAML atau TOML untuk runtime config.
- File config: `config.conf` (gitignored), template: `config.conf.example`.
- Struktur section: `[google]` → `service_account_file`.
- Validasi: path ke service account JSON harus exist — raise `FileNotFoundError` jika tidak.

---

## 💾 Database (CSV)

- CSV sebagai "database" sederhana — **bukan** SQLite atau database lain.
- File: `data/submissions.csv` (auto-created dengan headers).
- Operasi: load all → filter / upsert → save.
- Upsert logic: cari by `url`, jika ada update `status` + `updated_at`, jika tidak append.
- Encoding: UTF-8, newline: `""` (platform-neutral).
- Gunakan `csv.reader` / `csv.writer` standard library.

---

## 🌐 Sitemap Parsing

- Gunakan `aiohttp` untuk fetch, `lxml.etree` untuk parse XML.
- Handle 2 jenis sitemap:
  - `<urlset>` → regular sitemap (extract `<url>/<loc>`)
  - `<sitemapindex>` → index sitemap (extract `<sitemap>/<loc>`, lalu rekursif)
- XML namespace: `{"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}`
- Track `visited_sitemaps` untuk hindari infinite loop.
- User-Agent: `GSC-AutoSubmit/1.0`

---

## 🔄 Google Indexing API

- Auth: Service Account (`google.oauth2.service_account.Credentials`)
- Scope: `https://www.googleapis.com/auth/indexing`
- API: `indexing` v3 → `urlNotifications().publish()`
- Request body: `{"url": url, "type": "URL_UPDATED"}`
- Rate limiting: Retry dengan exponential backoff (2s, 4s, 8s) — max 3 retries.
- Quota default: 200 requests/day.

---

## 🧪 Testing & Running

```bash
# Install dependencies
uv sync

# Run CLI
uv run python main.py example.com
uv run python main.py https://example.com/sitemap.xml
uv run python main.py example.com --config /path/to/config.conf
uv run python main.py example.com --db /path/to/db.csv
uv run python main.py example.com -v   # verbose mode
```

---

## ⚠️ Hal yang TIDAK Boleh Dilakukan

1. **Jangan** ganti `argparse` dengan `click` atau `typer` tanpa approval.
2. **Jangan** ganti CSV database dengan SQLite atau database lain tanpa approval.
3. **Jangan** gunakan `requests` — project ini sepenuhnya async (`aiohttp`).
4. **Jangan** gunakan `print()` — gunakan `console` (Rich) atau `logger`.
5. **Jangan** hardcode credentials atau paths — semua harus dari `config.conf`.
6. **Jangan** commit file `config.conf`, `*.json` (service account), atau folder `data/`.
7. **Jangan** mengubah author attribution di module docstrings.
8. **Jangan** menambahkan dependency baru tanpa alasan kuat dan approval.

---

## ✅ Checklist Saat Menulis Kode Baru

- [ ] Semua fungsi memiliki type annotations lengkap?
- [ ] Docstring yang deskriptif di setiap fungsi publik?
- [ ] Menggunakan `logger` untuk logging internal?
- [ ] Menggunakan `console` (Rich) untuk output ke user?
- [ ] Error handling yang proper (specific exceptions, tidak silent catch)?
- [ ] Async function untuk semua I/O operations?
- [ ] Import mengikuti urutan: stdlib → third-party → local?
- [ ] Konsisten dengan naming convention project?
- [ ] Tidak menambahkan dependency baru yang tidak diperlukan?
- [ ] File baru ditempatkan di folder yang sesuai (core/models/services)?
