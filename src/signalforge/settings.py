"""Environment-only SignalForge configuration."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path


class ConfigurationError(Exception):
    """Safe configuration failure without secret values."""


@dataclass(frozen=True, slots=True)
class Settings:
    """Validated runtime settings with secret-safe representation."""

    telegram_api_id: int = field(repr=False)
    telegram_api_hash: str = field(repr=False)
    telegram_session_path: Path = field(repr=False)
    telegram_chat: str | int
    database_url: str = field(repr=False)


def load_settings(environ: Mapping[str, str]) -> Settings:
    """Validate required values without reading dotenv files."""
    api_id_raw = _required(environ, "SIGNALFORGE_TELEGRAM_API_ID")
    try:
        api_id = int(api_id_raw)
    except ValueError:
        raise ConfigurationError("SIGNALFORGE_TELEGRAM_API_ID must be an integer") from None
    if api_id < 1:
        raise ConfigurationError("SIGNALFORGE_TELEGRAM_API_ID must be positive")

    session_path = Path(_required(environ, "SIGNALFORGE_TELEGRAM_SESSION_PATH")).expanduser()
    if not session_path.is_absolute():
        raise ConfigurationError("SIGNALFORGE_TELEGRAM_SESSION_PATH must be absolute")

    chat_raw = _required(environ, "SIGNALFORGE_TELEGRAM_CHAT")
    chat: str | int = int(chat_raw) if chat_raw.lstrip("-").isdigit() else chat_raw
    return Settings(
        telegram_api_id=api_id,
        telegram_api_hash=_required(environ, "SIGNALFORGE_TELEGRAM_API_HASH"),
        telegram_session_path=session_path,
        telegram_chat=chat,
        database_url=_required(environ, "SIGNALFORGE_DATABASE_URL"),
    )


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name)
    if not value:
        raise ConfigurationError(f"{name} is required")
    return value
