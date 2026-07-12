"""Tests for environment-only settings."""

import pytest

from signalforge.settings import ConfigurationError, load_settings


def valid_environment() -> dict[str, str]:
    return {
        "SIGNALFORGE_TELEGRAM_API_ID": "12345",
        "SIGNALFORGE_TELEGRAM_API_HASH": "api-secret-canary",
        "SIGNALFORGE_TELEGRAM_SESSION_PATH": "/tmp/session-secret-canary",
        "SIGNALFORGE_TELEGRAM_CHAT": "-100123",
        "SIGNALFORGE_DATABASE_URL": "postgresql+psycopg://secret-canary@localhost/db",
    }


def test_loads_settings_and_redacts_repr() -> None:
    settings = load_settings(valid_environment())

    assert settings.telegram_api_id == 12345
    assert settings.telegram_chat == -100123
    representation = repr(settings)
    assert "api-secret-canary" not in representation
    assert "session-secret-canary" not in representation
    assert "postgresql+psycopg" not in representation


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("SIGNALFORGE_TELEGRAM_API_ID", "not-an-int"),
        ("SIGNALFORGE_TELEGRAM_API_ID", "0"),
        ("SIGNALFORGE_TELEGRAM_API_HASH", ""),
        ("SIGNALFORGE_TELEGRAM_SESSION_PATH", "relative.session"),
        ("SIGNALFORGE_TELEGRAM_CHAT", ""),
        ("SIGNALFORGE_DATABASE_URL", ""),
    ],
)
def test_rejects_invalid_settings_without_echoing_values(name: str, value: str) -> None:
    environment = valid_environment()
    environment[name] = value

    with pytest.raises(ConfigurationError) as captured:
        load_settings(environment)

    assert "secret-canary" not in str(captured.value)
