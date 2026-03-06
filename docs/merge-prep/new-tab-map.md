# New-Tab Integration Map (Startup Watch)

## Feature overview

This repository does **not** contain front-end tab code (no React/Next pages/components in-tree).
Its role for the future Searchbar3 "new tab" is a **data producer**:

- collect startup signals from configured sources
- normalize, filter, deduplicate
- emit CSV artifacts (`startup_watch/output/*.csv`)

For integration, Searchbar3 should treat Sourcing101 as an ingestion/export subsystem and consume the exported dataset (or a future API wrapper around the same pipeline).

## Entry points and execution path

- CLI entrypoint: `startup_watch/startup_watch.py`
  - parses `--config`
  - calls pipeline
  - writes CSV
- Pipeline orchestrator: `startup_watch/pipeline.py`
  - `load_config(path)`
  - `collect_signals(config)`
  - `run_pipeline(config)`
  - `write_csv(signals, output_dir)`

## Data/API dependencies

- External HTTP feeds/pages via adapters in `startup_watch/adapters/*.py`
- Config contract via:
  - `startup_watch/config.yaml`
  - `startup_watch/config.github.yaml`
- Data model contract:
  - `startup_watch/schema.py::StartupSignal`
- Transformation stages:
  - `startup_watch/filters.py`
  - `startup_watch/dedup.py`
  - `startup_watch/enrichment.py`

## Shared primitives/utilities (integration-relevant)

- `startup_watch/schema.py` — canonical stage normalization and output field contract
- `startup_watch/adapters/base.py` and `startup_watch/adapters/utils.py` — adapter scaffolding/utilities
- `startup_watch/logger.py` — structured logging pattern for long-running source collection

## Feature flags/toggles

Primary toggles are YAML `enabled` fields on adapter blocks in config files.
Special integration-sensitive toggles:

- `linkedin.enabled` (auth-bound; disabled in CI-safe mode)
- `linkedin_manual.enabled`
- `linkedin_enrichment.enabled`
- `playwright_fallback.enabled`
- pipeline retry/delay controls under `pipeline.*`

## Exact file list with purpose

### Core execution
- `startup_watch/startup_watch.py` — CLI entrypoint
- `startup_watch/pipeline.py` — orchestration and CSV emission
- `startup_watch/schema.py` — normalized signal schema
- `startup_watch/filters.py` — category/stage/exclusion filtering
- `startup_watch/dedup.py` — dedup strategy
- `startup_watch/enrichment.py` — non-source enrichment pass
- `startup_watch/logger.py` — logging helper

### Config and automation
- `startup_watch/config.yaml` — local/full config
- `startup_watch/config.github.yaml` — CI-safe config
- `.github/workflows/startup_watch.yml` — scheduled + manual CI run, writes latest artifact
- `startup_watch/README.md` — runbook

### Produced artifacts used by future UI integration
- `startup_watch/output/latest.csv`
- `startup_watch/output/startup_watch_*.csv`

## Coupling assessment and safe refactor notes

- UI coupling in this repo: **none** (no tab/page/component code present).
- System coupling that matters for integration:
  - large adapter import/wiring surface in `pipeline.py`
  - CSV-column contract in `write_csv`
- No code refactor was applied in this phase because coupling is currently data-contract based and stable; behavior-preserving extraction opportunities are documented in `conflict-matrix.md`.
