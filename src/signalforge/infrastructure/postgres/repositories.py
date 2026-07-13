"""PostgreSQL repository implementations."""

from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Engine
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from signalforge.application.errors import FatalImportError, ImportErrorCode, MessageImportError
from signalforge.application.models import (
    ImportCounts,
    ImportSummary,
    PersistedMessage,
    StoreOutcome,
)
from signalforge.digest.models import DigestContent, DigestMessage, MessageLink
from signalforge.infrastructure.postgres.schema import (
    daily_digests,
    message_links,
    telegram_import_runs,
    telegram_messages,
)


def _count_values(counts: ImportCounts) -> dict[str, int]:
    return {
        "processed_count": counts.processed,
        "new_count": counts.new,
        "existing_count": counts.existing,
        "skipped_count": counts.skipped,
        "error_count": counts.errors,
    }


class SqlAlchemyMessageRepository:
    """Insert Telegram messages with source-key idempotency."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def store(self, message: PersistedMessage) -> StoreOutcome:
        statement = (
            insert(telegram_messages)
            .values(
                source_chat_id=message.source_chat_id,
                source_message_id=message.source_message_id,
                sent_at=message.sent_at,
                sender_id=message.sender_id,
                sender_display_name=message.sender_display_name,
                text=message.text,
                attachment_type=message.attachment_type,
                reply_to_message_id=message.reply_to_message_id,
            )
            .on_conflict_do_nothing(constraint="uq_telegram_messages_source")
            .returning(telegram_messages.c.id)
        )
        try:
            with self._engine.begin() as connection:
                inserted_id = connection.execute(statement).scalar_one_or_none()
        except DBAPIError as error:
            if error.connection_invalidated:
                raise FatalImportError(ImportErrorCode.DATABASE) from None
            raise MessageImportError from None
        except SQLAlchemyError:
            raise FatalImportError(ImportErrorCode.DATABASE) from None
        return StoreOutcome.NEW if inserted_id is not None else StoreOutcome.EXISTING


class SqlAlchemyImportRunRepository:
    """Persist import run progress and terminal state."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def start(self, source_chat_ref: str) -> UUID:
        run_id = uuid4()
        statement = telegram_import_runs.insert().values(
            id=run_id,
            source_chat_ref=source_chat_ref,
            status="running",
            started_at=datetime.now(UTC),
        )
        self._execute(statement)
        return run_id

    def checkpoint(self, run_id: UUID, counts: ImportCounts) -> None:
        statement = (
            telegram_import_runs.update()
            .where(telegram_import_runs.c.id == run_id)
            .values(**_count_values(counts))
        )
        self._execute(statement)

    def finish(self, summary: ImportSummary) -> None:
        values: dict[str, object] = {
            **_count_values(summary.counts),
            "status": summary.status.value,
            "finished_at": datetime.now(UTC),
            "error_code": summary.error_code,
        }
        statement = (
            telegram_import_runs.update()
            .where(telegram_import_runs.c.id == summary.run_id)
            .values(**values)
        )
        self._execute(statement)

    def _execute(self, statement: sa.Executable) -> None:
        try:
            with self._engine.begin() as connection:
                connection.execute(statement)
        except SQLAlchemyError:
            raise FatalImportError(ImportErrorCode.DATABASE) from None


class SqlAlchemyDigestRepository:
    """Read daily messages and idempotently persist links and digests."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def messages_between(self, start: datetime, end: datetime) -> Sequence[DigestMessage]:
        statement = (
            sa.select(
                telegram_messages.c.id,
                telegram_messages.c.source_message_id,
                telegram_messages.c.sent_at,
                telegram_messages.c.text,
            )
            .where(telegram_messages.c.sent_at >= start, telegram_messages.c.sent_at < end)
            .order_by(telegram_messages.c.sent_at, telegram_messages.c.id)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return tuple(
            DigestMessage(
                id=row["id"],
                source_message_id=row["source_message_id"],
                sent_at=row["sent_at"],
                text=row["text"],
            )
            for row in rows
        )

    def store_links(self, links: Sequence[MessageLink]) -> None:
        if not links:
            return
        values = [{"message_id": link.message_id, "url": link.url} for link in links]
        statement = (
            insert(message_links)
            .values(values)
            .on_conflict_do_nothing(constraint="uq_message_links_message_url")
        )
        with self._engine.begin() as connection:
            connection.execute(statement)

    def save_digest(self, content: DigestContent) -> None:
        values: dict[str, object] = {
            "digest_date": content.digest_date,
            "timezone": content.timezone,
            "message_count": content.message_count,
            "link_count": content.link_count,
            "markdown": content.markdown,
            "model": content.model,
        }
        statement = insert(daily_digests).values(id=uuid4(), **values)
        statement = statement.on_conflict_do_update(
            index_elements=[daily_digests.c.digest_date],
            set_={**values, "updated_at": sa.func.now()},
        )
        with self._engine.begin() as connection:
            connection.execute(statement)
