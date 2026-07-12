# Telegram history import — decisions

## DEC-001: Use an MTProto user session for history import

- **Date:** 2026-07-12
- **Status:** Accepted
- **Context:** Для initial import требуется прочитать сообщения, существовавшие до запуска SignalForge.
- **Decision:** Использовать Telethon с авторизованной пользовательской session; Telegram-бот не используется для этой операции.
- **Alternatives:** Bot API; ручной Telegram Desktop export.
- **Consequences:** Потребуются Telegram API ID/hash и особо защищаемый session-файл; будущий бот остаётся отдельной feature.
- **Related requirements/tasks:** REQ-001, REQ-002, REQ-008, REQ-010.

## DEC-002: Recover through idempotent replay

- **Date:** 2026-07-12
- **Status:** Accepted
- **Context:** Импорт должен продолжаться после прерывания и не создавать дубликаты.
- **Decision:** Использовать уникальный `(source_chat_id, source_message_id)` и `INSERT ... ON CONFLICT DO NOTHING`; повторный запуск перечитывает доступную историю.
- **Alternatives:** Отдельный checkpoint последнего message ID; обновление существующих записей.
- **Consequences:** Реализация проще и устойчива к неточному checkpoint, но повторный запуск снова запрашивает историю у Telegram.
- **Related requirements/tasks:** REQ-004, REQ-005, REQ-006; AC-004, AC-005.

## DEC-003: Keep the importer synchronous outside the Telegram adapter

- **Date:** 2026-07-12
- **Status:** Accepted
- **Context:** Источник отдаёт сообщения последовательно, а ожидаемый первоначальный объём невелик.
- **Decision:** Application service и PostgreSQL adapter используют синхронные интерфейсы; event loop Telethon инкапсулирован source adapter.
- **Alternatives:** Полностью async application и SQLAlchemy adapter.
- **Consequences:** Меньше конкурентной сложности; параллельный импорт нескольких источников потребует пересмотра границы.
- **Related requirements/tasks:** REQ-001, REQ-002, REQ-006.
