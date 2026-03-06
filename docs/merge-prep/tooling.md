# Tooling and Reproducibility

## Runtime/toolchain snapshot

- Python: `3.9.6` (host)
- pip: `21.2.4`
- pytest: `8.3.3`
- flake8: `7.1.1`
- git: `2.50.1`

> Note: `pyproject.toml` declares `requires-python >=3.10`; local runtime currently uses 3.9.6. Final integration should align runner + local env to 3.10+.

## Package manager and dependency files

- Package manager: `pip`
- Dependency files:
  - `requirements.txt` (runtime, pinned)
  - `requirements-dev.txt` (dev tools, pinned, includes runtime)
- Lockfile: **none present** (Python pip flow). Deterministic installs depend on pinned requirements and stable indexes.

## Build / test / lint / run commands

From `Makefile`:

- install: `python3 -m pip install -r requirements-dev.txt`
- lint: `python -m flake8 startup_watch/ --max-line-length=100`
- test: `python -m pytest tests/ -q`
- run-ci: `python startup_watch/startup_watch.py --config startup_watch/config.github.yaml`
- run-local: `python startup_watch/startup_watch.py --config startup_watch/config.yaml`

## Required env/config inputs

- Config files:
  - `startup_watch/config.github.yaml` (CI-safe)
  - `startup_watch/config.yaml` (local/full)
- Optional env files:
  - `.env.example` (template)
- Optional runtime env vars used by selected adapters:
  - `LINKEDIN_EMAIL`
  - `LINKEDIN_PASSWORD`
  - `OPENAI_API_KEY`
  - browser profile values when LinkedIn/manual enrichment is enabled

## Determinism notes for merge prep

- Inputs are mostly external feeds; output row counts are expected to vary by run.
- Reproducibility target for integration should be command-level determinism (same commands, same schema/output format, stable CI-safe adapter enablement), not fixed row count.
