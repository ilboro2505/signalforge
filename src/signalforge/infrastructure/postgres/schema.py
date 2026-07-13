"""SQLAlchemy Core schema for SignalForge persistence."""

import sqlalchemy as sa

metadata = sa.MetaData()

telegram_messages = sa.Table(
    "telegram_messages",
    metadata,
    sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
    sa.Column("source_chat_id", sa.BigInteger, nullable=False),
    sa.Column("source_message_id", sa.BigInteger, nullable=False),
    sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("sender_id", sa.BigInteger, nullable=True),
    sa.Column("sender_display_name", sa.Text, nullable=True),
    sa.Column("text", sa.Text, nullable=False),
    sa.Column("attachment_type", sa.Text, nullable=True),
    sa.Column("reply_to_message_id", sa.BigInteger, nullable=True),
    sa.Column(
        "imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.UniqueConstraint("source_chat_id", "source_message_id", name="uq_telegram_messages_source"),
    sa.Index("ix_telegram_messages_sent_at", "sent_at"),
)

telegram_import_runs = sa.Table(
    "telegram_import_runs",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("source_chat_ref", sa.Text, nullable=False),
    sa.Column("status", sa.Text, nullable=False),
    sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    sa.Column("processed_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("new_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("existing_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("skipped_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("error_count", sa.Integer, nullable=False, server_default="0"),
    sa.Column("error_code", sa.Text, nullable=True),
    sa.CheckConstraint(
        "status IN ('running', 'success', 'partial', 'failed')",
        name="ck_telegram_import_runs_status",
    ),
    sa.CheckConstraint(
        "processed_count >= 0 AND new_count >= 0 AND existing_count >= 0 "
        "AND skipped_count >= 0 AND error_count >= 0",
        name="ck_telegram_import_runs_non_negative_counts",
    ),
)

message_links = sa.Table(
    "message_links",
    metadata,
    sa.Column("id", sa.BigInteger, sa.Identity(), primary_key=True),
    sa.Column(
        "message_id",
        sa.BigInteger,
        sa.ForeignKey("telegram_messages.id", ondelete="CASCADE"),
        nullable=False,
    ),
    sa.Column("url", sa.Text, nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.UniqueConstraint("message_id", "url", name="uq_message_links_message_url"),
)

daily_digests = sa.Table(
    "daily_digests",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("digest_date", sa.Date, nullable=False, unique=True),
    sa.Column("timezone", sa.Text, nullable=False),
    sa.Column("message_count", sa.Integer, nullable=False),
    sa.Column("link_count", sa.Integer, nullable=False),
    sa.Column("markdown", sa.Text, nullable=False),
    sa.Column("model", sa.Text, nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.Column(
        "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    ),
    sa.CheckConstraint(
        "message_count >= 0 AND link_count >= 0",
        name="ck_daily_digests_non_negative_counts",
    ),
)
