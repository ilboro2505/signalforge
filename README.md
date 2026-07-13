# SignalForge

SignalForge — персональная система для преобразования потока сообщений и материалов в структурированную базу знаний.

Первый планируемый сценарий — анализ Telegram-чата об LLM, AI-native разработке и coding agents: импорт истории, обработка новых сообщений, извлечение полезных ссылок и подготовка кратких дайджестов.

## MVP

Текущий CLI импортирует доступную историю настроенного Telegram-чата в PostgreSQL, извлекает HTTP/HTTPS-ссылки за выбранный локальный день и создаёт русский Markdown-дайджест через Responses-compatible LLM API.

## Project context

Исходные вводные и рабочие вопросы находятся в [`docs/project-context/`](docs/project-context/). Они сохраняют контекст проекта, но не являются утверждёнными требованиями.

После создания SDD-инфраструктуры источником истины будут документы в `specs/`.

## Operations

- [Импорт истории Telegram](docs/operations/telegram-history-import.md)
- [Ежедневный Markdown-дайджест](docs/operations/daily-digest.md)

После установки и применения миграций доступны команды:

```bash
signalforge import-history
signalforge generate-digest
signalforge generate-digest --date 2026-07-12
```
