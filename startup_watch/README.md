# Startup Watch (Supply Chain, Manufacturing, Industrial, AgTech)

Lightweight local runner to discover pre-seed, seed, and Series A startups from multiple sources, enrich basic data, and export to CSV.

## What it does
- Scans configured sources (LinkedIn search URLs, YC Directory, StartupStream, VC portfolio pages, optional Crunchbase free links).
- Extracts company names and basic signals.
- Enriches with website metadata (title/description) and simple stage inference.
- Writes a deduped CSV.

## Setup
1. Install Python 3.10+.
2. Create a virtualenv and install deps:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. If you want LinkedIn scraping via your logged-in session, install Playwright browsers:
   ```bash
   python -m playwright install
   ```

## Configure
Edit `startup_watch/config.yaml`:
- Add your LinkedIn boolean search URLs (Posts tab, sorted by Latest).
- Add YC batch and categories.
- Add VC portfolio URLs.
- Optional: set your Chrome profile path for LinkedIn session reuse.

## Run
```bash
python startup_watch/startup_watch.py --config startup_watch/config.yaml
```

CSV will be written to `startup_watch/output/startup_watch_<timestamp>.csv`.

## GitHub Actions (Public Sources Only)
This repo includes a workflow that runs weekly (Mondays at 9:00 AM PST) and on-demand via manual dispatch.
It uses `startup_watch/config.github.yaml` with LinkedIn disabled and uploads the CSV as a workflow artifact.

## Notes
- LinkedIn scraping is best-effort and depends on page structure. If it fails, run the script with `--linkedin-manual` to parse a saved HTML file exported from your browser.
- Respect site terms. This tool is intended for your personal research.
