# Daily knowledge digest — verification

## Acceptance traceability

| Criterion | Evidence |
|---|---|
| AC-001 | timezone/day unit tests and explicit/default-date CLI tests |
| AC-002 | URL normalization unit test and PostgreSQL duplicate-link integration test |
| AC-003 | fake generator input assertions, required-section validation and source-ID validation |
| AC-004 | empty-day service test verifies zero generator calls and deterministic file |
| AC-005 | atomic writer rerun test and PostgreSQL digest upsert integration test |
| AC-006 | secret-safe settings repr, provider error and CLI canary tests |
| AC-007 | digest CLI success/failure JSON and exit-code tests |

## Verification profiles

- Offline profile covers day selection, extraction, orchestration, LLM request/response parsing, configuration, CLI output, static analysis, dependency audit and package build without external credentials.
- PostgreSQL profile applies migrations from base through head and back to base against a disposable PostgreSQL 17 database; it verifies interval reads, link idempotency and digest upsert.
- Production provider connectivity is intentionally not automated because it requires a real secret and can incur external cost. The operations guide defines the real invocation after local configuration.

## Commands

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
python -m pip_audit -r requirements.lock
python -m build
```

The full database profile uses `python -m pytest --require-postgres` with `SIGNALFORGE_TEST_DATABASE_URL` pointing to the disposable database.

## Recorded result

Verified 2026-07-13: clean hash-locked installation passed 45 offline tests; the disposable PostgreSQL 17 profile passed all 49 tests. Ruff check/format, strict mypy, package build and dependency audit also passed; the audit reported no known vulnerabilities.
