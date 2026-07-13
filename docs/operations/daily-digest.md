# Daily digest operations

## Prerequisites

- установленный SignalForge и применённые PostgreSQL migrations;
- импортированные сообщения Telegram;
- API key и model ID для Responses-compatible LLM provider.

SignalForge читает только environment текущего процесса и не загружает `.env`. Не передавайте ключи в аргументах CLI, не храните их в репозитории и ограничьте права на локальный файл с переменными.

## Configure

```bash
export SIGNALFORGE_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost/signalforge'
export SIGNALFORGE_LLM_API_KEY='YOUR_PROVIDER_KEY'
export SIGNALFORGE_LLM_MODEL='YOUR_MODEL_ID'
export SIGNALFORGE_LLM_BASE_URL='https://api.openai.com/v1'
export SIGNALFORGE_TIMEZONE='Europe/Moscow'
export SIGNALFORGE_DIGEST_OUTPUT_DIR="$HOME/.local/share/signalforge/digests"
```

`SIGNALFORGE_LLM_BASE_URL` должен быть абсолютным HTTPS URL. Model ID задаётся явно: приложение не выбирает и не меняет модель автоматически.

## Generate

Предыдущий локальный день:

```bash
.venv/bin/python -m signalforge generate-digest
```

Явная дата в настроенной timezone:

```bash
.venv/bin/python -m signalforge generate-digest --date 2026-07-12
```

Команда печатает один JSON-объект. Успех возвращает exit `0`, дату, counts и путь `YYYY-MM-DD.md`; любая ошибка возвращает exit `1` и безопасный `error_code`. Для пустого дня создаётся детерминированный файл без LLM-вызова. Повторный успешный запуск заменяет файл атомарно и обновляет одну запись даты в PostgreSQL.

## Schedule with cron

Создайте вне репозитория protected environment file и wrapper, доступные только вашему OS user. Wrapper должен экспортировать переменные выше, перейти в каталог проекта и выполнить:

```bash
/absolute/path/to/signalforge/.venv/bin/python -m signalforge generate-digest
```

Пример crontab для запуска ежедневно в 01:05 системного времени:

```cron
5 1 * * * /absolute/path/to/signalforge-run-digest >> /absolute/path/to/signalforge-digest.log 2>&1
```

Установите wrapper и environment file в режим `chmod 700` и `chmod 600` соответственно. Cron определяет момент запуска, а `SIGNALFORGE_TIMEZONE` — календарный день выборки.

## Schedule with launchd

На macOS создайте user LaunchAgent, который запускает тот же protected wrapper, с `StartCalendarInterval` hour `1` и minute `5`. Не помещайте provider key или database URL непосредственно в tracked plist; wrapper должен получать их из protected environment file вне репозитория.

После загрузки LaunchAgent сначала запустите wrapper вручную и проверьте JSON и созданный Markdown-файл.

## Failure behavior

- `configuration_error`: отсутствует или невалидна настройка;
- `invalid_date`: `--date` не соответствует `YYYY-MM-DD`;
- `llm_error`: provider/network/response failure;
- `internal_error`: database, filesystem или непредвиденная ошибка.

Provider response body, API key и database URL не выводятся. При LLM failure существующий успешный Markdown-файл не заменяется.
