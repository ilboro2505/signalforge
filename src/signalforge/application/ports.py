"""Ports required by the Telegram history import use case."""

from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from signalforge.application.models import (
    ImportCounts,
    ImportSummary,
    PersistedMessage,
    SourceMessage,
    StoreOutcome,
)


class TelegramHistorySource(Protocol):
    """Yield normalized messages from oldest to newest."""

    def messages(self) -> Iterable[SourceMessage]: ...


class MessageRepository(Protocol):
    """Persist messages idempotently."""

    def store(self, message: PersistedMessage) -> StoreOutcome: ...


class ImportRunRepository(Protocol):
    """Persist import-run lifecycle and progress."""

    def start(self, source_chat_ref: str) -> UUID: ...

    def checkpoint(self, run_id: UUID, counts: ImportCounts) -> None: ...

    def finish(self, summary: ImportSummary) -> None: ...
