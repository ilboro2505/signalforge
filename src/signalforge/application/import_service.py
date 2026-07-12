"""Orchestrate one idempotent Telegram history import."""

from dataclasses import dataclass
from datetime import UTC

from signalforge.application.errors import FatalImportError, MessageImportError
from signalforge.application.models import (
    ImportCounts,
    ImportStatus,
    ImportSummary,
    PersistedMessage,
    SourceMessage,
    StoreOutcome,
)
from signalforge.application.ports import (
    ImportRunRepository,
    MessageRepository,
    TelegramHistorySource,
)


@dataclass(slots=True)
class _MutableCounts:
    processed: int = 0
    new: int = 0
    existing: int = 0
    skipped: int = 0
    errors: int = 0

    def snapshot(self) -> ImportCounts:
        return ImportCounts(
            processed=self.processed,
            new=self.new,
            existing=self.existing,
            skipped=self.skipped,
            errors=self.errors,
        )


class HistoryImportService:
    """Classify, map, and store a stream of normalized source messages."""

    def __init__(
        self,
        source: TelegramHistorySource,
        messages: MessageRepository,
        runs: ImportRunRepository,
        *,
        checkpoint_interval: int = 100,
    ) -> None:
        if checkpoint_interval < 1:
            raise ValueError("checkpoint_interval must be positive")
        self._source = source
        self._messages = messages
        self._runs = runs
        self._checkpoint_interval = checkpoint_interval

    def run(self, source_chat_ref: str) -> ImportSummary:
        """Execute one import and return a safe terminal summary."""
        run_id = self._runs.start(source_chat_ref)
        counts = _MutableCounts()
        error_code: str | None = None

        try:
            for source_message in self._source.messages():
                self._process_one(source_message, counts)
                if counts.processed % self._checkpoint_interval == 0:
                    self._runs.checkpoint(run_id, counts.snapshot())
        except FatalImportError as error:
            status = ImportStatus.FAILED
            error_code = error.code.value
        else:
            status = ImportStatus.PARTIAL if counts.errors else ImportStatus.SUCCESS

        summary = ImportSummary(
            run_id=run_id,
            source_chat_ref=source_chat_ref,
            status=status,
            counts=counts.snapshot(),
            error_code=error_code,
        )
        self._runs.finish(summary)
        return summary

    def _process_one(self, source: SourceMessage, counts: _MutableCounts) -> None:
        counts.processed += 1

        if source.is_service or not source.text:
            counts.skipped += 1
            return

        try:
            message = self._map_message(source)
            outcome = self._messages.store(message)
        except (MessageImportError, ValueError):
            counts.errors += 1
            return

        if outcome is StoreOutcome.NEW:
            counts.new += 1
        elif outcome is StoreOutcome.EXISTING:
            counts.existing += 1
        else:
            counts.errors += 1

    @staticmethod
    def _map_message(source: SourceMessage) -> PersistedMessage:
        if source.source_message_id < 1:
            raise ValueError("source_message_id must be positive")
        if source.sent_at.tzinfo is None or source.sent_at.utcoffset() is None:
            raise ValueError("sent_at must be timezone-aware")

        return PersistedMessage(
            source_chat_id=source.source_chat_id,
            source_message_id=source.source_message_id,
            sent_at=source.sent_at.astimezone(UTC),
            text=source.text or "",
            sender_id=source.sender_id,
            sender_display_name=source.sender_display_name,
            attachment_type=source.attachment_type,
            reply_to_message_id=source.reply_to_message_id,
        )
