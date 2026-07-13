"""PostgreSQL integration tests for SignalForge repositories."""

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import Engine

from signalforge.application.models import (
    ImportCounts,
    ImportStatus,
    ImportSummary,
    PersistedMessage,
    StoreOutcome,
)
from signalforge.digest.models import DigestContent, MessageLink
from signalforge.infrastructure.postgres.repositories import (
    SqlAlchemyDigestRepository,
    SqlAlchemyImportRunRepository,
    SqlAlchemyMessageRepository,
)
from signalforge.infrastructure.postgres.schema import (
    daily_digests,
    message_links,
    telegram_import_runs,
    telegram_messages,
)

pytestmark = pytest.mark.integration


def persisted_message(message_id: int = 7) -> PersistedMessage:
    return PersistedMessage(
        source_chat_id=-100123,
        source_message_id=message_id,
        sent_at=datetime(2026, 7, 12, 12, 30, tzinfo=UTC),
        text="caption",
        sender_id=None,
        sender_display_name=None,
        attachment_type="photo",
        reply_to_message_id=6,
    )


def test_message_repository_is_idempotent_and_preserves_fields(postgres_engine: Engine) -> None:
    repository = SqlAlchemyMessageRepository(postgres_engine)

    assert repository.store(persisted_message()) is StoreOutcome.NEW
    assert repository.store(persisted_message()) is StoreOutcome.EXISTING

    with postgres_engine.connect() as connection:
        rows = connection.execute(sa.select(telegram_messages)).mappings().all()
    assert len(rows) == 1
    assert rows[0]["source_chat_id"] == -100123
    assert rows[0]["source_message_id"] == 7
    assert rows[0]["text"] == "caption"
    assert rows[0]["attachment_type"] == "photo"
    assert rows[0]["reply_to_message_id"] == 6
    assert rows[0]["sender_id"] is None


def test_import_run_repository_persists_checkpoint_and_terminal_state(
    postgres_engine: Engine,
) -> None:
    repository = SqlAlchemyImportRunRepository(postgres_engine)
    run_id = repository.start("safe-chat-ref")
    repository.checkpoint(run_id, ImportCounts(processed=2, new=1, skipped=1))
    summary = ImportSummary(
        run_id=run_id,
        source_chat_ref="safe-chat-ref",
        status=ImportStatus.PARTIAL,
        counts=ImportCounts(processed=3, new=1, skipped=1, errors=1),
        error_code=None,
    )

    repository.finish(summary)

    with postgres_engine.connect() as connection:
        row = (
            connection.execute(
                sa.select(telegram_import_runs).where(telegram_import_runs.c.id == run_id)
            )
            .mappings()
            .one()
        )
    assert row["status"] == "partial"
    assert row["finished_at"] is not None
    assert row["processed_count"] == 3
    assert row["new_count"] == 1
    assert row["skipped_count"] == 1
    assert row["error_count"] == 1


def test_database_constraints_reject_invalid_run(postgres_engine: Engine) -> None:
    with pytest.raises(sa.exc.IntegrityError), postgres_engine.begin() as connection:
        connection.execute(
            telegram_import_runs.insert().values(
                id=uuid4(),
                source_chat_ref="chat",
                status="unknown",
                started_at=datetime.now(UTC),
            )
        )


def test_digest_repository_filters_links_and_upserts(postgres_engine: Engine) -> None:
    message_repository = SqlAlchemyMessageRepository(postgres_engine)
    assert message_repository.store(persisted_message(7)) is StoreOutcome.NEW
    assert message_repository.store(persisted_message(8)) is StoreOutcome.NEW
    repository = SqlAlchemyDigestRepository(postgres_engine)

    messages = repository.messages_between(
        datetime(2026, 7, 12, tzinfo=UTC), datetime(2026, 7, 13, tzinfo=UTC)
    )
    link = MessageLink(messages[0].id, messages[0].source_message_id, "https://example.com")
    repository.store_links([link])
    repository.store_links([link])
    repository.save_digest(_digest_content("first"))
    repository.save_digest(_digest_content("second"))

    with postgres_engine.connect() as connection:
        stored_links = connection.execute(sa.select(message_links)).mappings().all()
        digests = connection.execute(sa.select(daily_digests)).mappings().all()
    assert [message.source_message_id for message in messages] == [7, 8]
    assert len(stored_links) == 1
    assert len(digests) == 1
    assert digests[0]["markdown"] == "second"


def _digest_content(markdown: str) -> DigestContent:
    return DigestContent(
        digest_date=date(2026, 7, 12),
        timezone="Europe/Moscow",
        message_count=2,
        link_count=1,
        markdown=markdown,
        model="fake",
    )
