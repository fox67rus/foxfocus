"""seed users

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-26

Пока аутентификации нет, user_id приходит в запросе, поэтому базовые
пользователи должны существовать сразу после миграций.
"""

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PUBLIC_IDS = ("u_1", "u_2")

users = sa.table(
    "users",
    sa.column("public_id", sa.String),
    sa.column("created_at", sa.DateTime),
)


def upgrade() -> None:
    created_at = datetime.now(UTC)
    op.bulk_insert(
        users,
        [{"public_id": public_id, "created_at": created_at} for public_id in PUBLIC_IDS],
    )


def downgrade() -> None:
    op.execute(users.delete().where(users.c.public_id.in_(PUBLIC_IDS)))
