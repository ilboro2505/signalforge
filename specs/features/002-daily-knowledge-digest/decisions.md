# Daily knowledge digest — decisions

## DEC-001: External scheduling boundary

- **Date:** 2026-07-12
- **Status:** Accepted
- **Decision:** Предоставить идемпотентную CLI-команду; ежедневный запуск делегировать cron/launchd.
- **Consequences:** MVP остаётся простым и локальным; пользователь отдельно включает расписание.

## DEC-002: Responses-compatible HTTP adapter

- **Date:** 2026-07-12
- **Status:** Accepted
- **Decision:** Изолировать LLM за typed port и использовать configurable Responses endpoint без provider SDK.
- **Consequences:** Меньше dependencies; adapter обязан самостоятельно валидировать и безопасно разбирать JSON.
