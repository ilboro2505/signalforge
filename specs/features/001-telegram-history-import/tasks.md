# Telegram history import — tasks

## Definition of Done

- реализован только scope выбранной задачи;
- связанные requirements и acceptance criteria выполнены;
- релевантные тесты и документация добавлены или обновлены;
- применимые test, lint, format, type-check, security и build проверки успешно пройдены;
- значимые решения зафиксированы;
- секреты и чувствительные данные отсутствуют;
- checkbox обновлён только после выполнения всех критериев задачи.

## Tasks

- [x] **TASK-001: Создать проверяемый Python project skeleton**
  - Scope: создать packaged `src/signalforge` layout, `pyproject.toml`, runtime/dev dependency declarations, CLI-заглушку без продуктового поведения, базовую конфигурацию pytest/Ruff/mypy и smoke tests импорта/сборки; дополнить `.gitignore` generated artifacts.
  - Related requirements/criteria: инфраструктурная зависимость для REQ-001–REQ-010; не реализует acceptance criteria самостоятельно.
  - Verification: `python -m pytest`, `python -m ruff check .`, `python -m ruff format --check .`, `python -m mypy src tests`, `python -m build`.
  - Dependencies: approved spec и completed design.

- [x] **TASK-002: Реализовать application model и import service**
  - Scope: определить typed source/repository ports, `SourceMessage`, persisted message input, run summary/status и синхронный orchestration service; реализовать classification, counters, per-message isolation и fatal-error behavior с fake-based unit tests.
  - Related requirements/criteria: REQ-002, REQ-003, REQ-006–REQ-009; AC-001, AC-003, AC-005, AC-006, AC-008.
  - Verification: unit tests application layer плюс все обязательные проверки.
  - Dependencies: TASK-001.

- [x] **TASK-003: Добавить PostgreSQL schema и repositories**
  - Scope: создать Alembic migration для `telegram_messages`/`telegram_import_runs`, SQLAlchemy Core mappings и repositories с `ON CONFLICT DO NOTHING`, batch transactions и run lifecycle; добавить disposable-PostgreSQL integration tests.
  - Related requirements/criteria: REQ-003–REQ-006, REQ-009; AC-002–AC-005, AC-008.
  - Verification: migration upgrade/downgrade tests, uniqueness/idempotency/restart integration tests и все обязательные проверки с `SIGNALFORGE_TEST_DATABASE_URL`.
  - Dependencies: TASK-001, TASK-002.

- [x] **TASK-004: Реализовать безопасный Telethon history adapter**
  - Scope: реализовать oldest-first user-session source, peer resolution, message normalization, media-type mapping, service-message detection и безопасное преобразование Telegram errors; не загружать media и не логировать session/credentials; тестировать synthetic objects без сети.
  - Related requirements/criteria: REQ-001–REQ-003, REQ-007, REQ-008, REQ-010; AC-001–AC-003, AC-006, AC-007, AC-009.
  - Verification: adapter mapping/error/redaction tests и все обязательные проверки без Telegram network access.
  - Dependencies: TASK-001, TASK-002; DEC-001, DEC-003.

- [x] **TASK-005: Собрать CLI и configuration boundary**
  - Scope: реализовать environment-only settings validation, composition root, `import-history` command, JSON summary, documented exit codes и allow-listed safe diagnostics; интегрировать source/service/repositories.
  - Related requirements/criteria: REQ-001, REQ-008–REQ-010; AC-007–AC-009.
  - Verification: CLI tests success/partial/failure/configuration, secret-canary scan captured output/logs и все обязательные проверки.
  - Dependencies: TASK-002, TASK-003, TASK-004.

- [x] **TASK-006: Проверить feature end-to-end и эксплуатационную документацию**
  - Scope: добавить локальную инструкцию PostgreSQL/migrations/session-path/import command без реальных секретов; зафиксировать hashed dependency locks; выполнить полную traceability verification и проверить clean install/build.
  - Related requirements/criteria: REQ-001–REQ-010; AC-001–AC-009.
  - Verification: все design commands, PostgreSQL integration profile, acceptance traceability matrix и ручная проверка документации без обращения к реальному Telegram.
  - Dependencies: TASK-001–TASK-005.
