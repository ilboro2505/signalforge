# Telegram history import operations

## Prerequisites

- Python 3.12–3.14;
- PostgreSQL;
- Telegram API ID/hash from `my.telegram.org`;
- a user account that can read the target chat.

Telegram credentials and session files are secrets. Keep them outside the repository, never paste them into documentation or logs, and restrict the session file to the current OS user.

## Install

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
```

## PostgreSQL and migrations

Create a dedicated database/user using your normal local PostgreSQL administration workflow. Export the URL in the current shell; SignalForge never loads `.env` automatically:

```bash
export SIGNALFORGE_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost/signalforge'
.venv/bin/python -m alembic upgrade head
```

## Create the Telegram user session once

Choose an absolute path outside the repository, for example `$HOME/.local/share/signalforge/telegram`. Export the API values and run Telethon interactively:

```bash
export SIGNALFORGE_TELEGRAM_API_ID='YOUR_API_ID'
export SIGNALFORGE_TELEGRAM_API_HASH='YOUR_API_HASH'
export SIGNALFORGE_TELEGRAM_SESSION_PATH="$HOME/.local/share/signalforge/telegram"

.venv/bin/python -c 'import os; from telethon.sync import TelegramClient; TelegramClient(os.environ["SIGNALFORGE_TELEGRAM_SESSION_PATH"], int(os.environ["SIGNALFORGE_TELEGRAM_API_ID"]), os.environ["SIGNALFORGE_TELEGRAM_API_HASH"]).start().disconnect()'
chmod 600 "$SIGNALFORGE_TELEGRAM_SESSION_PATH.session"
```

Do not commit the resulting `.session` file. If it is exposed, revoke the session from an official Telegram client.

## Run the import

```bash
export SIGNALFORGE_TELEGRAM_CHAT='CHAT_USERNAME_OR_NUMERIC_ID'
.venv/bin/python -m signalforge import-history
```

The command prints one JSON object:

- exit `0`: `success`;
- exit `2`: `partial`, with individual message errors;
- exit `1`: configuration, authorization, access, connection, database, or internal failure.

Running the same import again is safe: existing messages are counted but not duplicated.

## Verification

Default offline profile:

```bash
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m mypy src tests
.venv/bin/python -m pip_audit -r requirements.lock
.venv/bin/python -m build
```

Full PostgreSQL profile against a disposable database:

```bash
export SIGNALFORGE_TEST_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@localhost/signalforge_test'
.venv/bin/python -m pytest --require-postgres
```

Automated tests never connect to Telegram. A real-account smoke test must be run manually after local secrets are configured.
