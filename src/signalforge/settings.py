"""Environment-only SignalForge configuration."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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


@dataclass(frozen=True, slots=True)
class DigestSettings:
    """Validated digest settings with secrets excluded from repr."""

    database_url: str = field(repr=False)
    llm_api_key: str = field(repr=False)
    llm_model: str
    llm_base_url: str
    timezone: str
    output_dir: Path


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


def load_digest_settings(environ: Mapping[str, str]) -> DigestSettings:
    """Validate digest-only configuration without requiring Telegram credentials."""
    timezone = environ.get("SIGNALFORGE_TIMEZONE", "Europe/Moscow")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise ConfigurationError("SIGNALFORGE_TIMEZONE must be a valid IANA timezone") from None

    base_url = environ.get("SIGNALFORGE_LLM_BASE_URL", "https://api.openai.com/v1")
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ConfigurationError("SIGNALFORGE_LLM_BASE_URL must be an absolute HTTPS URL")

    return DigestSettings(
        database_url=_required(environ, "SIGNALFORGE_DATABASE_URL"),
        llm_api_key=_required(environ, "SIGNALFORGE_LLM_API_KEY"),
        llm_model=_required(environ, "SIGNALFORGE_LLM_MODEL"),
        llm_base_url=base_url,
        timezone=timezone,
        output_dir=Path(environ.get("SIGNALFORGE_DIGEST_OUTPUT_DIR", "digests")).expanduser(),
    )


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name)
    if not value:
        raise ConfigurationError(f"{name} is required")
    return value
