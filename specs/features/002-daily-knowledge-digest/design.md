# Daily knowledge digest — technical design

## Related specification

- Feature: `002-daily-knowledge-digest`, approved 2026-07-12 by `user`.

## Design summary

CLI `signalforge generate-digest [--date YYYY-MM-DD]` вычисляет локальный день через `zoneinfo`, читает Telegram messages из PostgreSQL, извлекает canonical URLs, idempotently сохраняет их, вызывает provider-neutral `DigestGenerator`, атомарно пишет Markdown и upsert-ит digest metadata/content.

Production LLM adapter выполняет HTTPS POST к configurable `<base-url>/responses` с bearer key, `model`, `instructions` и `input`. Ответ извлекается из top-level `output_text` либо из text content элементов `output`. Model обязателен в environment и не имеет динамического default. OpenAI документирует text-capable models через Responses API в [официальном model catalog](https://developers.openai.com/api/docs/models).

## Components

- `DailyDigestService`: orchestration, empty template, section validation.
- `extract_urls`: pure standard-library normalization.
- `DigestRepository`: date-range messages, link insert, digest upsert.
- `ResponsesDigestGenerator`: provider HTTP boundary with safe errors.
- `AtomicMarkdownWriter`: temp file in target directory plus `os.replace`.
- CLI/settings/composition extensions.

## Data model

Migration `0002_daily_digest` adds:

- `message_links(id, message_id FK, url, created_at)` unique `(message_id, url)`;
- `daily_digests(id UUID, digest_date date unique, timezone, message_count, link_count, markdown, model, created_at, updated_at)`.

## Prompt and input limits

Messages are ordered by `sent_at, id`. Each line contains timestamp, source message ID and text. Input is capped deterministically at 200 messages and 60,000 characters; truncation is reported in the prompt. The model is instructed not to invent links/facts and to return sections `# SignalForge — YYYY-MM-DD`, `## Кратко`, `## Основные темы`, `## Полезные ссылки`.

## Security

- API key and DB URL are secret fields excluded from repr/output.
- Provider exceptions and response bodies are reduced to `llm_error`.
- HTTP timeout is 60 seconds; redirects are not manually followed.
- Markdown uses only selected message text and model output; no secret settings are included.

## Verification

```bash
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m mypy src tests
python -m pip_audit -r requirements.lock
python -m build
```

PostgreSQL profile uses `python -m pytest --require-postgres`. LLM tests use a local fake transport and never call a provider.

## Decisions

- Use standard-library `urllib` rather than a new HTTP dependency.
- Use explicit CLI scheduling boundary; document cron/launchd instead of embedding a daemon.
- Store generated Markdown in PostgreSQL and filesystem for traceability and direct reading.

## Open questions

Нет блокирующих технических вопросов.
