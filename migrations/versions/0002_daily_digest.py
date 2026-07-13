"""Create daily digest tables."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_daily_digest"
down_revision: str | None = "0001_telegram_history_import"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "message_links",
        sa.Column("id", sa.BigInteger(), sa.Identity(), primary_key=True),
        sa.Column(
            "message_id",
            sa.BigInteger(),
            sa.ForeignKey("telegram_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("message_id", "url", name="uq_message_links_message_url"),
    )
    op.create_table(
        "daily_digests",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("digest_date", sa.Date(), nullable=False, unique=True),
        sa.Column("timezone", sa.Text(), nullable=False),
        sa.Column("message_count", sa.Integer(), nullable=False),
        sa.Column("link_count", sa.Integer(), nullable=False),
        sa.Column("markdown", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "message_count >= 0 AND link_count >= 0",
            name="ck_daily_digests_non_negative_counts",
        ),
    )


def downgrade() -> None:
    op.drop_table("daily_digests")
    op.drop_table("message_links")
