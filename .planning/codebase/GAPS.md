# GAPS

1. Monolithic `startup_watch.py` should be modularized (schema/pipeline/adapters/logging).
2. No robust adapter abstraction with per-source class contracts yet.
3. Test coverage is minimal.
4. Requirements pinning and dev dependency separation can be improved.
5. Legacy OCR folder uses hardcoded absolute paths and needs portability cleanup.
6. Observability/logging consistency can be improved (structured logs everywhere).
