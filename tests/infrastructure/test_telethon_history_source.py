"""Network-free tests for the Telethon history adapter."""

from dataclasses import dataclass, field
from datetime import UTC, datetime

import pytest
from telethon import errors

from signalforge.application.errors import FatalImportError, ImportErrorCode
from signalforge.infrastructure.telegram.history_source import TelethonHistorySource


@dataclass
class FakeSender:
    first_name: str | None = None
    last_name: str | None = None
    title: str | None = None
    username: str | None = None


@dataclass
class FakeMessage:
    id: int
    chat_id: int = -100123
    date: datetime = datetime(2026, 7, 12, 12, tzinfo=UTC)
    message: str | None = "text"
    sender_id: int | None = 42
    sender: object | None = field(default_factory=lambda: FakeSender("Ada", "Lovelace"))
    media: object | None = None
    reply_to_msg_id: int | None = None
    action: object | None = None


@dataclass
class FakeClient:
    items: list[object] = field(default_factory=list)
    authorized: bool = True
    failure: Exception | None = None
    connected: bool = False
    disconnected: bool = False
    requested: list[tuple[str | int, bool]] = field(default_factory=list)

    def connect(self) -> None:
        self.connected = True
        if self.failure is not None:
            raise self.failure

    def disconnect(self) -> None:
        self.disconnected = True

    def is_user_authorized(self) -> bool:
        return self.authorized

    def iter_messages(self, entity: str | int, *, reverse: bool) -> list[object]:
        self.requested.append((entity, reverse))
        return self.items


def test_maps_messages_oldest_first_without_downloading_media() -> None:
    photo = type("MessageMediaPhoto", (), {})()
    client = FakeClient(
        items=[
            FakeMessage(1),
            FakeMessage(
                2,
                message="caption",
                sender_id=None,
                sender=FakeSender(title="SignalForge Chat"),
                media=photo,
                reply_to_msg_id=1,
            ),
        ]
    )

    messages = list(TelethonHistorySource(client, "chat-name").messages())

    assert [item.source_message_id for item in messages] == [1, 2]
    assert messages[0].sender_display_name == "Ada Lovelace"
    assert messages[1].sender_display_name == "SignalForge Chat"
    assert messages[1].attachment_type == "photo"
    assert messages[1].reply_to_message_id == 1
    assert client.requested == [("chat-name", True)]
    assert client.connected and client.disconnected


def test_marks_service_messages_and_missing_optional_fields() -> None:
    service_type = type("MessageService", (), {})
    raw = service_type()
    raw.id = 3
    raw.chat_id = -100123
    raw.date = datetime(2026, 7, 12, tzinfo=UTC)
    raw.message = None
    raw.sender_id = None
    raw.sender = None
    raw.media = None
    raw.reply_to_msg_id = None
    raw.action = object()

    result = list(TelethonHistorySource(FakeClient([raw]), -100123).messages())

    assert result[0].is_service
    assert result[0].sender_id is None
    assert result[0].sender_display_name is None
    assert result[0].text is None


@pytest.mark.parametrize(
    ("failure", "expected_code"),
    [
        (OSError("secret session path"), ImportErrorCode.TELEGRAM_CONNECTION),
        (
            errors.UnauthorizedError(None, "secret auth payload"),
            ImportErrorCode.TELEGRAM_AUTH,
        ),
        (errors.ChannelPrivateError(None), ImportErrorCode.TELEGRAM_ACCESS),
        (errors.FloodWaitError(None, capture=5), ImportErrorCode.TELEGRAM_RATE_LIMIT),
    ],
)
def test_maps_external_errors_to_safe_codes(
    failure: Exception,
    expected_code: ImportErrorCode,
) -> None:
    source = TelethonHistorySource(FakeClient(failure=failure), "chat")

    with pytest.raises(FatalImportError) as captured:
        list(source.messages())

    assert captured.value.code is expected_code
    assert "secret" not in str(captured.value)


def test_rejects_unauthorized_session_without_iterating() -> None:
    client = FakeClient(authorized=False)

    with pytest.raises(FatalImportError) as captured:
        list(TelethonHistorySource(client, "chat").messages())

    assert captured.value.code is ImportErrorCode.TELEGRAM_AUTH
    assert client.requested == []
    assert client.disconnected
