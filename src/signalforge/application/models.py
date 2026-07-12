"""Technology-independent models for Telegram history import."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


@dataclass(frozen=True, slots=True)
class SourceMessage:
    """Normalized message emitted by a history source in source order."""

    source_chat_id: int
    source_message_id: int
    sent_at: datetime
    text: str | None
    sender_id: int | None = None
    sender_display_name: str | None = None
    attachment_type: str | None = None
    reply_to_message_id: int | None = None
    is_service: bool = False


@dataclass(frozen=True, slots=True)
class PersistedMessage:
    """Validated message passed to persistence."""

    source_chat_id: int
    source_message_id: int
    sent_at: datetime
    text: str
    sender_id: int | None
    sender_display_name: str | None
    attachment_type: str | None
    reply_to_message_id: int | None


class StoreOutcome(StrEnum):
    """Result of an idempotent message insert."""

    NEW = "new"
    EXISTING = "existing"


class ImportStatus(StrEnum):
    """Terminal state of an import run."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ImportCounts:
    """Immutable snapshot of import counters."""

    processed: int = 0
    new: int = 0
    existing: int = 0
    skipped: int = 0
    errors: int = 0

    def is_consistent(self) -> bool:
        """Return whether categorized messages equal all processed messages."""
        return self.processed == self.new + self.existing + self.skipped + self.errors


@dataclass(frozen=True, slots=True)
class ImportSummary:
    """Safe terminal result returned by the import service."""

    run_id: UUID
    source_chat_ref: str
    status: ImportStatus
    counts: ImportCounts
    error_code: str | None = None
