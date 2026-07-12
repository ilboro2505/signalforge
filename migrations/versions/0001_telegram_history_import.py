"""Create Telegram history import tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_telegram_history_import"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telegram_messages",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column("source_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("source_message_id", sa.BigInteger(), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sender_id", sa.BigInteger(), nullable=True),
        sa.Column("sender_display_name", sa.Text(), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("attachment_type", sa.Text(), nullable=True),
        sa.Column("reply_to_message_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "source_chat_id",
            "source_message_id",
            name="uq_telegram_messages_source",
        ),
    )
    op.create_index("ix_telegram_messages_sent_at", "telegram_messages", ["sent_at"])
    op.create_table(
        "telegram_import_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_chat_ref", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("existing_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.Text(), nullable=True),
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


def downgrade() -> None:
    op.drop_table("telegram_import_runs")
    op.drop_index("ix_telegram_messages_sent_at", table_name="telegram_messages")
    op.drop_table("telegram_messages")
