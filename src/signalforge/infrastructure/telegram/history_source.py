"""Safe Telethon adapter for oldest-first history iteration."""

import re
from collections.abc import Iterable
from contextlib import suppress
from datetime import datetime
from typing import Protocol, cast

from telethon import errors

from signalforge.application.errors import FatalImportError, ImportErrorCode
from signalforge.application.models import SourceMessage


class SyncTelethonClient(Protocol):
    """Minimal synchronous Telethon surface used by the adapter."""

    def connect(self) -> object: ...

    def disconnect(self) -> object: ...

    def is_user_authorized(self) -> bool: ...

    def iter_messages(self, entity: str | int, *, reverse: bool) -> Iterable[object]: ...


class TelethonHistorySource:
    """Read one user-visible Telegram history without downloading media."""

    def __init__(self, client: SyncTelethonClient, chat_ref: str | int) -> None:
        self._client = client
        self._chat_ref = chat_ref

    def messages(self) -> Iterable[SourceMessage]:
        """Yield normalized messages from oldest to newest."""
        connected = False
        try:
            self._client.connect()
            connected = True
            if not self._client.is_user_authorized():
                raise FatalImportError(ImportErrorCode.TELEGRAM_AUTH)
            for raw in self._client.iter_messages(self._chat_ref, reverse=True):
                yield _normalize_message(raw)
        except FatalImportError:
            raise
        except (errors.UnauthorizedError, errors.AuthKeyError):
            raise FatalImportError(ImportErrorCode.TELEGRAM_AUTH) from None
        except (
            errors.ChannelPrivateError,
            errors.ChatAdminRequiredError,
            errors.UserNotParticipantError,
        ):
            raise FatalImportError(ImportErrorCode.TELEGRAM_ACCESS) from None
        except errors.FloodWaitError:
            raise FatalImportError(ImportErrorCode.TELEGRAM_RATE_LIMIT) from None
        except (ConnectionError, OSError, TimeoutError, errors.RPCError):
            raise FatalImportError(ImportErrorCode.TELEGRAM_CONNECTION) from None
        finally:
            if connected:
                with suppress(Exception):
                    self._client.disconnect()


def _normalize_message(raw: object) -> SourceMessage:
    sender = getattr(raw, "sender", None)
    text = cast(str | None, getattr(raw, "message", None))
    sent_at = cast(datetime, getattr(raw, "date", None))
    return SourceMessage(
        source_chat_id=int(getattr(raw, "chat_id", 0) or 0),
        source_message_id=int(getattr(raw, "id", 0) or 0),
        sent_at=sent_at,
        text=text,
        sender_id=_optional_int(cast(int | None, getattr(raw, "sender_id", None))),
        sender_display_name=_sender_display_name(sender),
        attachment_type=_attachment_type(getattr(raw, "media", None)),
        reply_to_message_id=_optional_int(cast(int | None, getattr(raw, "reply_to_msg_id", None))),
        is_service=type(raw).__name__ == "MessageService"
        or getattr(raw, "action", None) is not None,
    )


def _optional_int(value: int | None) -> int | None:
    return value


def _sender_display_name(sender: object | None) -> str | None:
    if sender is None:
        return None
    first_name = getattr(sender, "first_name", None)
    last_name = getattr(sender, "last_name", None)
    personal_name = " ".join(part for part in (first_name, last_name) if part)
    if personal_name:
        return personal_name
    for attribute in ("title", "username"):
        value = getattr(sender, attribute, None)
        if value:
            return str(value)
    return None


def _attachment_type(media: object | None) -> str | None:
    if media is None or type(media).__name__ == "MessageMediaEmpty":
        return None
    class_name = type(media).__name__
    short_name = class_name.removeprefix("MessageMedia")
    return re.sub(r"(?<!^)(?=[A-Z])", "_", short_name).lower() or "unknown"
