"""Unit tests for the technology-independent history import service."""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from signalforge.application.errors import (
    FatalImportError,
    ImportErrorCode,
    MessageImportError,
)
from signalforge.application.import_service import HistoryImportService
from signalforge.application.models import (
    ImportCounts,
    ImportStatus,
    ImportSummary,
    PersistedMessage,
    SourceMessage,
    StoreOutcome,
)


def message(message_id: int, text: str | None = "text", **kwargs: object) -> SourceMessage:
    values: dict[str, object] = {
        "source_chat_id": -100123,
        "source_message_id": message_id,
        "sent_at": datetime(2026, 7, 12, message_id % 24, tzinfo=UTC),
        "text": text,
    }
    values.update(kwargs)
    return SourceMessage(**values)  # type: ignore[arg-type]


@dataclass
class FakeSource:
    items: list[SourceMessage]
    fatal_after: int | None = None

    def messages(self) -> Iterable[SourceMessage]:
        for index, item in enumerate(self.items):
            if self.fatal_after == index:
                raise FatalImportError(ImportErrorCode.TELEGRAM_CONNECTION)
            yield item
        if self.fatal_after == len(self.items):
            raise FatalImportError(ImportErrorCode.TELEGRAM_CONNECTION)


@dataclass
class FakeMessageRepository:
    outcomes: dict[int, StoreOutcome] = field(default_factory=dict)
    failures: set[int] = field(default_factory=set)
    stored: list[PersistedMessage] = field(default_factory=list)

    def store(self, item: PersistedMessage) -> StoreOutcome:
        if item.source_message_id in self.failures:
            raise MessageImportError
        self.stored.append(item)
        return self.outcomes.get(item.source_message_id, StoreOutcome.NEW)


@dataclass
class FakeRunRepository:
    run_id: UUID = field(default_factory=uuid4)
    started_with: list[str] = field(default_factory=list)
    checkpoints: list[ImportCounts] = field(default_factory=list)
    finished: list[ImportSummary] = field(default_factory=list)

    def start(self, source_chat_ref: str) -> UUID:
        self.started_with.append(source_chat_ref)
        return self.run_id

    def checkpoint(self, run_id: UUID, counts: ImportCounts) -> None:
        assert run_id == self.run_id
        self.checkpoints.append(counts)

    def finish(self, summary: ImportSummary) -> None:
        self.finished.append(summary)


def build_service(
    items: list[SourceMessage],
    *,
    messages: FakeMessageRepository | None = None,
    runs: FakeRunRepository | None = None,
    fatal_after: int | None = None,
    checkpoint_interval: int = 100,
) -> tuple[HistoryImportService, FakeMessageRepository, FakeRunRepository]:
    message_repository = messages or FakeMessageRepository()
    run_repository = runs or FakeRunRepository()
    service = HistoryImportService(
        FakeSource(items, fatal_after=fatal_after),
        message_repository,
        run_repository,
        checkpoint_interval=checkpoint_interval,
    )
    return service, message_repository, run_repository


def test_imports_messages_in_source_order_with_all_metadata() -> None:
    items = [
        message(1, "first", sender_id=10, sender_display_name="Ada"),
        message(
            2,
            "caption",
            attachment_type="photo",
            reply_to_message_id=1,
            sender_id=None,
        ),
    ]
    service, repository, runs = build_service(items)

    summary = service.run("safe-chat-ref")

    assert [item.source_message_id for item in repository.stored] == [1, 2]
    assert repository.stored[1].attachment_type == "photo"
    assert repository.stored[1].reply_to_message_id == 1
    assert repository.stored[1].sender_id is None
    assert summary.status is ImportStatus.SUCCESS
    assert summary.counts == ImportCounts(processed=2, new=2)
    assert summary.counts.is_consistent()
    assert runs.started_with == ["safe-chat-ref"]
    assert runs.finished == [summary]


def test_classifies_existing_skipped_and_empty_history() -> None:
    repository = FakeMessageRepository(outcomes={1: StoreOutcome.EXISTING})
    service, repository, _ = build_service(
        [message(1), message(2, None), message(3, "service", is_service=True)],
        messages=repository,
    )

    summary = service.run("chat")

    assert summary.counts == ImportCounts(processed=3, existing=1, skipped=2)
    assert summary.status is ImportStatus.SUCCESS
    assert [item.source_message_id for item in repository.stored] == [1]

    empty_service, _, _ = build_service([])
    empty_summary = empty_service.run("empty")
    assert empty_summary.status is ImportStatus.SUCCESS
    assert empty_summary.counts == ImportCounts()


def test_isolates_invalid_and_repository_message_errors() -> None:
    invalid_timestamp = datetime(2026, 7, 12)
    repository = FakeMessageRepository(failures={2})
    service, repository, _ = build_service(
        [message(1), message(2), message(3, sent_at=invalid_timestamp), message(4)],
        messages=repository,
    )

    summary = service.run("chat")

    assert [item.source_message_id for item in repository.stored] == [1, 4]
    assert summary.status is ImportStatus.PARTIAL
    assert summary.counts == ImportCounts(processed=4, new=2, errors=2)
    assert summary.counts.is_consistent()


def test_fatal_source_error_finishes_failed_without_discarding_progress() -> None:
    service, repository, runs = build_service(
        [message(1), message(2)],
        fatal_after=1,
    )

    summary = service.run("chat")

    assert [item.source_message_id for item in repository.stored] == [1]
    assert summary.status is ImportStatus.FAILED
    assert summary.error_code == "telegram_connection_error"
    assert summary.counts == ImportCounts(processed=1, new=1)
    assert runs.finished == [summary]


def test_checkpoints_on_configured_processed_interval() -> None:
    service, _, runs = build_service(
        [message(1), message(2, None), message(3)],
        checkpoint_interval=2,
    )

    summary = service.run("chat")

    assert runs.checkpoints == [ImportCounts(processed=2, new=1, skipped=1)]
    assert summary.counts == ImportCounts(processed=3, new=2, skipped=1)


def test_rejects_non_positive_checkpoint_interval() -> None:
    with pytest.raises(ValueError, match="checkpoint_interval must be positive"):
        HistoryImportService(
            FakeSource([]),
            FakeMessageRepository(),
            FakeRunRepository(),
            checkpoint_interval=0,
        )
