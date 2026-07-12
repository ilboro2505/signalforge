"""Safe application-level import errors."""

from enum import StrEnum


class ImportErrorCode(StrEnum):
    """Allow-listed fatal error codes safe to persist and display."""

    TELEGRAM_AUTH = "telegram_auth_error"
    TELEGRAM_ACCESS = "telegram_access_error"
    TELEGRAM_RATE_LIMIT = "telegram_rate_limit_error"
    TELEGRAM_CONNECTION = "telegram_connection_error"
    DATABASE = "database_error"


class FatalImportError(Exception):
    """Stop an import while exposing only a safe error code."""

    def __init__(self, code: ImportErrorCode) -> None:
        super().__init__(code.value)
        self.code = code


class MessageImportError(Exception):
    """Reject one message while allowing the import to continue."""
