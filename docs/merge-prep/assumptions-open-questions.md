# Assumptions and Open Questions

## Assumptions

1. Searchbar3 final integration will consume Sourcing101 outputs as data source for the new tab.
2. Sourcing101 remains Python-based and should not be converted to JS/TS during initial merge.
3. Initial integration goal is stability/compatibility, not architecture redesign.
4. CI may run separate jobs for Python pipeline and Searchbar3 web stack.

## Open questions

1. Integration mode: subtree, submodule, or direct file import into Searchbar3?
2. Expected runtime boundary: execute pipeline in Searchbar3 CI only, or external scheduled runner + ingest artifact?
3. Canonical data contract for new tab: CSV only, or immediate JSON/API adapter layer?
4. Artifact publishing strategy: commit `latest.csv` vs CI artifact vs object storage?
5. Should legacy `SCM Companies PItchbook Extract/` be retained in initial merge scope?
6. Minimum supported Python version in merged repo runtime (3.10 vs 3.11)?

## Blockers (none hard)

- No hard blocker to prep completion.
- Final merge decisions depend on orchestration choices above.
