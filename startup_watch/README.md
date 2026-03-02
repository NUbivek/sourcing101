# Startup Watch

Config-driven startup sourcing pipeline for supply chain, manufacturing, AgTech, and industrial AI.

## Run

```bash
python startup_watch/startup_watch.py --config startup_watch/config.yaml
```

CI-safe mode:

```bash
python startup_watch/startup_watch.py --config startup_watch/config.github.yaml
```

## Current modular layout

- `startup_watch/schema.py`
- `startup_watch/pipeline.py`
- `startup_watch/filters.py`
- `startup_watch/dedup.py`
- `startup_watch/enrichment.py`
- `startup_watch/logger.py`
- `startup_watch/adapters/`
  - `base.py`
  - `yc.py`
  - `startupstream.py`
  - `linkedin.py` (local-only placeholder; auth-required)

## Tests

```bash
python -m pytest tests/ -q
```
