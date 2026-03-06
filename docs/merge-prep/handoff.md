# Handoff Package: Sourcing101 → Searchbar3 (Merge-Prep)

## Summary of prep changes

This branch prepares Sourcing101 for future cross-repo integration without performing the final merge.

Completed:
- baseline + tooling inventory
- mapping of integration-relevant "new tab" data surfaces
- compatibility/conflict matrix with risk scoring
- validation gates (lint/test/build + run-path notes)
- reproducibility and runbook notes for OpenClaw orchestration

## Recommended import sequence into Searchbar3

1. **Import docs first** (`docs/merge-prep/**`) so integration agent has context.
2. **Import pipeline subsystem** (`startup_watch/**`, `tests/**`, `requirements*.txt`, `pyproject.toml`).
3. **Run isolated Python gates** in Searchbar3 integration branch:
   - lint
   - tests
   - build
   - CI-safe pipeline run
4. **Wire UI/tab consumption** in Searchbar3 against CSV contract (or API shim).
5. **Only then** optimize internals/refactor module boundaries.

## Suggested checkpoints for rollback

Use these phase commits as checkpoints:

- Phase A: `ecb7a66` — baseline/tooling
- Phase B: `501870a` — new-tab map
- Phase C: `8791000` — conflict matrix
- Phase D: `3f29f0c` — validation/reproducibility fixes
- Phase E: _(this commit)_

## Integrate first vs later

### Integrate first (must-have)
- `startup_watch/` pipeline + configs
- `tests/`
- `requirements*.txt`, `pyproject.toml`
- `.github/workflows/startup_watch.yml`
- `docs/merge-prep/*`

### Integrate later (post-stabilization)
- structural refactor of `pipeline.py` adapter registry
- archival cleanup of `SCM Companies PItchbook Extract/`
- lockfile strategy (pip-tools/uv/poetry) if Searchbar3 requires stronger dependency pinning

## OpenClaw orchestration note

Do final cross-repo merge in a dedicated integration branch with explicit conflict-resolution commits; avoid squashing prep history so rollback checkpoints remain usable.
