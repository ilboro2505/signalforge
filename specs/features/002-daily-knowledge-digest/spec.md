---
feature_id: 002-daily-knowledge-digest
status: Approved
approved_by: user
approved_at: 2026-07-12
---

# Daily knowledge digest

## Summary

Извлекать ссылки из сохранённых Telegram-сообщений за локальный календарный день, создавать краткую LLM-выжимку и атомарно сохранять ежедневный Markdown-дайджест.

## User value

Пользователь получает один читаемый файл с главными темами и полезными материалами вместо ручного чтения всего дневного потока.

## Scope

### In scope

- выбор сообщений одного календарного дня в настроенной timezone;
- извлечение и сохранение HTTP/HTTPS ссылок с привязкой к исходным сообщениям;
- LLM-анализ выбранных сообщений через Responses-compatible API;
- Markdown-дайджест с обзором, темами и ссылками;
- повторный безопасный запуск для той же даты;
- CLI-команда, пригодная для ежедневного запуска cron/launchd.

### Out of scope

- встроенный scheduler/daemon;
- загрузка и анализ содержимого веб-страниц;
- semantic search, embeddings и topic history;
- доставка дайджеста ботом, email или web UI;
- автоматическая проверка фактов вне исходных сообщений.

## Requirements

- **REQ-001:** Пользователь может сгенерировать дайджест для явной даты или предыдущего локального дня по умолчанию.
- **REQ-002:** Границы дня вычисляются в настроенной IANA timezone, а выборка PostgreSQL выполняется по соответствующему UTC-интервалу.
- **REQ-003:** Из текста сообщений извлекаются только абсолютные HTTP/HTTPS URL; trailing punctuation и fragments не входят в canonical URL.
- **REQ-004:** Одинаковая canonical URL сохраняется не более одного раза для одного исходного сообщения; повторный запуск не создаёт дубликаты.
- **REQ-005:** LLM получает только дату, сообщения выбранного интервала и извлечённые ссылки и должен вернуть Markdown на русском языке.
- **REQ-006:** Итоговый Markdown содержит дату, краткий обзор, основные темы и список полезных ссылок с исходными Telegram message IDs.
- **REQ-007:** При отсутствии сообщений создаётся детерминированный пустой дайджест без LLM-вызова.
- **REQ-008:** Файл записывается атомарно как `<output-dir>/YYYY-MM-DD.md`; повторный успешный запуск заменяет файл и запись digest для даты.
- **REQ-009:** API key, database URL и полный provider error payload не выводятся и не сохраняются в digest.
- **REQ-010:** Команда сообщает JSON status, дату, число сообщений/ссылок и путь файла; failure не выдаётся за success.

## Acceptance criteria

- **AC-001** (covers REQ-001, REQ-002): Явная дата и default previous day дают правильный UTC half-open interval для `Europe/Moscow`.
- **AC-002** (covers REQ-003, REQ-004): Из смешанного текста сохраняются только нормализованные HTTP/HTTPS links без duplicates при повторном запуске.
- **AC-003** (covers REQ-005, REQ-006): Fake LLM получает только выбранные messages/links, а валидный Markdown содержит обязательные секции и source IDs.
- **AC-004** (covers REQ-007): Нулевая выборка не вызывает LLM и создаёт пустой шаблон.
- **AC-005** (covers REQ-008): Два успешных запуска одной даты оставляют один digest record и один целевой файл с последним содержимым.
- **AC-006** (covers REQ-009): Canary secrets отсутствуют в CLI output, Markdown и persisted digest.
- **AC-007** (covers REQ-010): CLI возвращает exit `0` и JSON для success, exit `1` и safe error code для failures.

## Constraints

- Источник сообщений — PostgreSQL tables feature `001-telegram-history-import`.
- Default timezone — `Europe/Moscow`.
- Model ID задаётся конфигурацией и не фиксируется спецификацией.
- External network используется только LLM adapter во время реального запуска.

## Edge cases and failure behavior

- URL с одинаковым scheme/host/path, но разными fragments считается одной ссылкой; query сохраняется.
- Невалидная дата/timezone/configuration завершает команду до LLM-вызова.
- LLM/network/response parse failure не заменяет существующий успешный digest.
- Ошибка atomic replace оставляет предыдущий файл без изменений.

## Dependencies

- Feature `001-telegram-history-import` в статусе `Implemented` или `Verified`.
- PostgreSQL migrations применены.

## Open questions

Нет блокирующих вопросов для минимальной CLI/Markdown версии.
