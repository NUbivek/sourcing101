# Conflict Matrix for Searchbar3 Integration

## Scope

This matrix assumes Sourcing101 remains a pipeline/data-export subsystem integrated into Searchbar3, where Searchbar3 hosts the UI tab.

## Likely conflict areas

| Area | Files/Surface | Risk | Why | Recommended resolution |
|---|---|---:|---|---|
| Python package layout | `startup_watch/**` | Medium | Searchbar3 may not be Python-first; repo conventions may differ | Integrate under a dedicated subdir (e.g., `services/startup_watch`) and keep entrypoint path stable |
| Dependency management | `requirements*.txt`, Python runtime | High | Sourcing101 expects Python toolchain; Searchbar3 likely JS/TS primary | Containerize or isolate Python job in CI; avoid mixing with Node lockfile lifecycle |
| CI workflow overlap | `.github/workflows/startup_watch.yml` | Medium | Naming/schedules/artifact conventions may conflict | Import as separate workflow name/job; avoid reusing existing workflow IDs |
| Output artifact path | `startup_watch/output/latest.csv` | Medium | Searchbar3 artifact strategy may differ | Keep output path configurable; consume via explicit path contract |
| Adapter orchestration file size | `startup_watch/pipeline.py` | Low | Large import/wiring surface increases merge friction | Prefer additive merges; postpone major refactor until post-integration |
| Legacy data directory | `SCM Companies PItchbook Extract/` | Medium | Large historical artifacts can create noisy diffs | Keep as-is initially; optionally move to archival path post-merge with dedicated PR |

## Explicit compatibility checks requested

### 1) Route collisions
- Current state in Sourcing101: no web routes/pages.
- Risk: **Low**.
- Integration note: route collisions are expected in Searchbar3 UI code, not this repo.

### 2) Component naming collisions
- Current state in Sourcing101: no React/UI components.
- Risk: **Low**.
- Integration note: collisions will occur only when importing/creating UI layer in Searchbar3.

### 3) CSS/design token conflicts
- Current state in Sourcing101: no CSS/design-token system.
- Risk: **Low**.
- Integration note: none from this repo directly.

### 4) Dependency/version mismatch
- Current state: Python stack pinned in `requirements*.txt`; project metadata says `>=3.10`; local host used 3.9.6 during validation.
- Risk: **High**.
- Resolution: enforce Python 3.10+ in integration runtime/CI and keep Python deps isolated from Node toolchain.

### 5) Config/CI mismatch
- Current state: dedicated YAML configs (`config.yaml`, `config.github.yaml`) + workflow `startup_watch.yml`.
- Risk: **Medium**.
- Resolution: preserve config file paths; avoid flattening into unrelated env conventions during initial merge.

## Recommended merge order from a risk perspective

1. Bring code/config first (`startup_watch/**`, requirements, tests).
2. Run Python validation in isolation.
3. Add/adjust CI workflow.
4. Wire Searchbar3 UI consumer against exported CSV contract.
5. Optimize/refactor internals only after green integration baseline.
