"""PostgreSQL integration tests for history import repositories."""

from datetime import UTC, datetime
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
from signalforge.infrastructure.postgres.repositories import (
    SqlAlchemyImportRunRepository,
    SqlAlchemyMessageRepository,
)
from signalforge.infrastructure.postgres.schema import telegram_import_runs, telegram_messages

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
