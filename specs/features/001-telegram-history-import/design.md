# Telegram history import — technical design

## Related specification

- Feature: `001-telegram-history-import`
- Approved status: `Approved` on 2026-07-12 by `user`

## Design summary

Реализовать packaged Python 3.12 application с CLI-командой `python -m signalforge import-history`. Команда использует авторизованную пользовательскую MTProto session через Telethon, последовательно читает историю от старых сообщений к новым и сохраняет подходящие сообщения в PostgreSQL через SQLAlchemy.

Telegram Bot API не используется для исторического импорта: метод [`messages.getHistory`](https://core.telegram.org/method/messages.getHistory) доступен только пользователям. Session считается секретом и хранится по пути вне репозитория.

Повторяемость и восстановление обеспечиваются уникальным ключом `(source_chat_id, source_message_id)` и PostgreSQL `INSERT ... ON CONFLICT DO NOTHING`. Отдельный checkpoint не нужен: повторный запуск безопасно проходит доступную историю заново и пропускает уже сохранённые записи.

## Technology choices

- Python 3.12 и `src/` layout.
- Стандартный `venv`/`pip` и `pyproject.toml`; дополнительный project manager не требуется.
- Telethon 1.x для MTProto user session и последовательного чтения истории.
- SQLAlchemy 2.x Core и синхронный Psycopg 3 для PostgreSQL.
- Alembic для версионируемых миграций.
- `argparse` и `os.environ` из стандартной библиотеки для CLI и конфигурации.
- Pytest, Ruff, mypy и pip-audit для проверок разработки.

Зависимости фиксируются совместимыми диапазонами в `pyproject.toml`; установленное дерево фиксируется requirements lock-файлами с hashes до реализации Telegram adapter.

## Components and responsibilities

```text
CLI
 ├─ Settings loader
 ├─ TelegramHistorySource (port)
 │    └─ TelethonHistorySource (adapter)
 └─ HistoryImportService
      ├─ Message classifier/mapper
      ├─ MessageRepository (port)
      │    └─ SqlAlchemyMessageRepository (adapter)
      └─ ImportRunRepository
```

### CLI

- Загружает и валидирует обязательные environment variables.
- Запускает один import run.
- Печатает в stdout один JSON summary без секретов.
- Возвращает exit code `0` для `success`, `2` для `partial`, `1` для fatal failure/configuration error.

### Settings loader

Обязательные переменные:

- `SIGNALFORGE_TELEGRAM_API_ID`;
- `SIGNALFORGE_TELEGRAM_API_HASH`;
- `SIGNALFORGE_TELEGRAM_SESSION_PATH`;
- `SIGNALFORGE_TELEGRAM_CHAT`;
- `SIGNALFORGE_DATABASE_URL`.

Значения API hash, database URL и session path не включаются в исключения, `repr`, логи или summary. `.env` автоматически не загружается.

### TelegramHistorySource

Асинхронные детали Telethon скрыты адаптером. Порт отдаёт нормализованный поток `SourceMessage` в порядке от старого к новому:

- chat ID;
- message ID;
- UTC timestamp;
- optional sender ID и display name;
- optional text/caption;
- optional attachment type;
- optional reply-to message ID;
- признак service message.

Адаптер не вызывает download media. Flood-wait обрабатывается только штатным ожиданием Telethon; бесконечные собственные retry не добавляются.

### HistoryImportService

- Создаёт запись import run.
- Увеличивает `processed_count` для каждого полученного элемента.
- Учитывает service messages и элементы без text/caption как `skipped_count`.
- Преобразует подходящий элемент в `TelegramMessage` и передаёт repository.
- Учитывает результат insert как `new_count` или `existing_count`.
- Изолирует ошибку преобразования/записи одного сообщения и учитывает её в `error_count`.
- Завершает run как `success`, `partial` или `failed` и возвращает summary.

### Repositories

Repository interfaces принадлежат application layer и не зависят от SQLAlchemy. PostgreSQL adapter выполняет parameterized statements. Вставка сообщения использует `ON CONFLICT DO NOTHING` по уникальному constraint и `RETURNING`, чтобы различить новую и существующую запись. Поддержка PostgreSQL upsert описана в [SQLAlchemy PostgreSQL dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert).

## Interfaces and data flow

1. CLI валидирует settings до открытия Telegram/DB соединений (`REQ-001`, `REQ-010`).
2. CLI создаёт adapters и передаёт их `HistoryImportService`.
3. Telegram adapter разрешает настроенный peer и начинает итерацию в oldest-first порядке (`REQ-002`, `AC-001`).
4. Service классифицирует каждый элемент, не загружая media (`REQ-003`, `AC-003`).
5. Repository атомарно вставляет запись или сообщает о конфликте (`REQ-004`–`REQ-006`, `AC-004`, `AC-005`).
6. Счётчики обновляются в памяти; состояние run сохраняется периодически вместе с message batches размером не более 100 записей.
7. После исчерпания потока или ошибки run финализируется, а CLI печатает summary (`REQ-008`, `REQ-009`).

Инвариант summary:

```text
processed_count = new_count + existing_count + skipped_count + error_count
```

## Data model changes

### `telegram_messages`

| Column | Type | Rules |
|---|---|---|
| `id` | bigint identity | primary key |
| `source_chat_id` | bigint | not null |
| `source_message_id` | bigint | not null |
| `sent_at` | timestamptz | not null, normalized to UTC |
| `sender_id` | bigint | nullable |
| `sender_display_name` | text | nullable |
| `text` | text | not null |
| `attachment_type` | text | nullable |
| `reply_to_message_id` | bigint | nullable; source-local reference, no FK |
| `imported_at` | timestamptz | not null, server default |

Unique constraint: `uq_telegram_messages_source(source_chat_id, source_message_id)`.

### `telegram_import_runs`

| Column | Type | Rules |
|---|---|---|
| `id` | uuid | primary key |
| `source_chat_ref` | text | non-secret configured identifier |
| `status` | text | `running`, `success`, `partial`, `failed` check constraint |
| `started_at` | timestamptz | not null |
| `finished_at` | timestamptz | nullable while running |
| `processed_count` | integer | non-negative |
| `new_count` | integer | non-negative |
| `existing_count` | integer | non-negative |
| `skipped_count` | integer | non-negative |
| `error_count` | integer | non-negative |
| `error_code` | text | nullable, allow-listed internal code |

Миграция `0001_telegram_history_import` создаёт обе таблицы, constraints и index по `telegram_messages(sent_at)` для будущей последовательной обработки. Downgrade удаляет только созданные этой миграцией объекты.

## Transaction and recovery behavior

- Run record создаётся отдельной committed transaction.
- Message inserts и обновление счётчиков run фиксируются batches до 100 обработанных элементов.
- Ошибка одной записи откатывает только её savepoint.
- Fatal Telegram/DB error прекращает чтение. Если DB доступна, run помечается `failed`; иначе незавершённый `running` run остаётся диагностическим следом.
- Новый запуск не зависит от прошлого run и восстанавливает полноту за счёт idempotent insert.

## Error handling and observability

- Внешние исключения преобразуются в allow-listed codes: `configuration_error`, `telegram_auth_error`, `telegram_access_error`, `telegram_rate_limit_error`, `telegram_connection_error`, `database_error`, `message_error`.
- Пользовательское сообщение содержит тип проблемы и безопасное действие, но не исходное exception payload, URL БД, API hash или session path.
- Логи структурированы и содержат run ID, event, безопасный chat reference и counters. Полный объект settings и объекты Telethon не логируются.
- Individual message errors логируют run ID и source message ID без содержимого сообщения.

## Security and privacy

- Session-файл создаётся и читается Telethon только по явно заданному пути вне репозитория; права файла документируются как user-only.
- API credentials и DB credentials поступают только через process environment.
- Session и API hash не сохраняются в PostgreSQL.
- SQL всегда parameterized.
- Тесты используют synthetic credentials/messages и не обращаются к Telegram.
- `.gitignore` продолжает блокировать `.env`, `*.session` и `*.session-journal`.
- Telethon session даёт доступ к аккаунту и рассматривается как credential; это согласуется с предупреждениями в [Telethon session documentation](https://docs.telethon.dev/en/stable/concepts/sessions.html).

## Verification strategy

### Automated tests

- Unit tests application service с fake source/repositories покрывают classification, counters, ordering contract, idempotency outcomes, per-message errors и fatal errors.
- Adapter mapping tests используют synthetic Telethon-like objects без сети.
- PostgreSQL integration tests применяют миграцию к disposable database и проверяют constraints, `ON CONFLICT`, batches и run states.
- CLI tests проверяют JSON summary, exit codes и redaction.
- Acceptance mapping:
  - `AC-001`–`AC-003`: source contract, mapping и integration tests;
  - `AC-004`, `AC-005`: PostgreSQL idempotency/restart tests;
  - `AC-006`: missing-author unit test;
  - `AC-007`: CLI fatal error/redaction tests;
  - `AC-008`: counter invariant tests;
  - `AC-009`: secret canary scan across captured logs, summary and persisted rows.

### Required commands

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
python -m pip_audit
python -m build
```

PostgreSQL integration tests require `SIGNALFORGE_TEST_DATABASE_URL`; tests that require it must fail with an actionable message rather than silently skip in the full verification profile.

## Alternatives considered

### Telegram Bot API

Отклонено для этой feature: Telegram документирует `messages.getHistory` как user-only. Бот остаётся возможным интерфейсом для будущих команд и доставки дайджестов, но не для первоначального чтения истории.

### Telegram Desktop export

Отклонено как основной путь: требует ручного экспорта и отдельного нестабильного parser format. Может стать отдельным offline adapter позднее.

### Async SQLAlchemy

Отклонено для первого importer: один последовательный source и небольшой объём не требуют дополнительной async DB сложности. Telethon adapter инкапсулирует свой event loop на границе.

### Explicit checkpoint

Отклонён: уникальный source key и повторный проход дают более простой и надёжный recovery для текущего объёма. Checkpoint можно добавить после измерения производительности больших историй.

## Risks and mitigations

- **Telegram rate limits:** не распараллеливать history requests; уважать штатный flood wait.
- **Session compromise:** хранить вне Git, не логировать и документировать отзыв session через Telegram clients.
- **Изменения Telethon API:** ограничить библиотеку совместимым major/minor range и изолировать в одном adapter.
- **Частично завершённый run:** idempotent restart восстанавливает сообщения; stale `running` остаётся видимым.
- **Непредвиденный тип сообщения:** классифицировать как skipped либо message error без остановки общего прохода.

## Open questions

Нет открытых технических вопросов, блокирующих декомпозицию.
