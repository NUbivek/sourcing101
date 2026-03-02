# SOURCING101 CUSTOM COMMANDS

Argument-based commands for OpenCode + Codex.

## Commands
- /src — Build/manage one adapter (`--new --test --list --status`)
- /batch — Build adapters in sequence (`--tier --list --resume --dry-run --limit --from`)
- /simplify — Refactor without behavior changes (`--file --module --adapter --target`)
- /enrich — Add enrichment function (`--field --source --test`)
- /run — Execute pipeline (`--config --source --dry-run --verbose`)
- /lsp — Configure/check/fix pyright (`--enable --strict --check --file --fix`)
- /fix — Fix adapter/test/CI (`--adapter --test --ci --reason`)
- /check — Read-only quality audit (`--full --adapter`)
- /stage — Run GSD lifecycle (`--plan --execute --verify --status --next`)

## Quick Reference
| Command | Flags | Use for |
|---------|-------|---------|
| /src | --new --test --list --status | Build or inspect a single adapter |
| /batch | --tier --list --resume --dry-run | Build a whole tier of adapters |
| /simplify | --file --module --adapter --target | Refactor code without behavior change |
| /enrich | --field --source --test | Add enrichment function to pipeline |
| /run | --config --source --dry-run | Execute pipeline, see results |
| /lsp | --enable --check --fix | Type checking with pyright |
| /fix | --adapter --test --ci | Fix broken adapter/test/CI |
| /check | --full --adapter | Read-only quality audit |
| /stage | --plan --execute --verify --status | Run GSD phase lifecycle |

## Codebase-specific rules
1. One adapter = one source file + one test file + two config entries + one atomic commit.
2. Never enable LinkedIn in CI config.
3. Stage values must be canonical: pre-seed|stealth|seed|series-a|series-b|series-c.
4. Keep `scm_pitchbook/` separate from `startup_watch/` work.
5. Use conventional commits.
