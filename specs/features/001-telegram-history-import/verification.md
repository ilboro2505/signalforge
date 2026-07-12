# Telegram history import — verification

## Acceptance traceability

| Criterion | Evidence |
|---|---|
| AC-001 | oldest-first adapter request and ordered service tests in `test_telethon_history_source.py` and `test_import_service.py` |
| AC-002 | mapping unit test and PostgreSQL field-preservation integration test |
| AC-003 | media caption/type adapter and application tests; adapter exposes no download operation |
| AC-004 | PostgreSQL repository double-insert integration test |
| AC-005 | idempotent existing outcome, durable per-message transactions and application fatal-progress test |
| AC-006 | missing sender mapping/service tests |
| AC-007 | Telethon error mapping and CLI safe fatal-output tests |
| AC-008 | application counter invariant and CLI JSON/exit-code tests |
| AC-009 | settings repr, adapter exception and CLI canary redaction tests |

## Verification profiles

- Offline profile covers application, Telegram adapter mapping, configuration, CLI output, static analysis, dependency audit and package build without external credentials.
- PostgreSQL profile applies migration upgrade/downgrade to a disposable database and covers constraints, persistence, idempotency and run lifecycle.
- Real Telegram connectivity is not automated because it requires the user's credentials and chat access. The operational guide defines the manual smoke test.
