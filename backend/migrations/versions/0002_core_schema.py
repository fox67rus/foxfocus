"""core schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-26

Таблицы ТЗ: users, tasks, notes, memory_facts, audit_runs.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("public_id", name=op.f("uq_users_public_id")),
    )
    op.create_table(
        "audit_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("input", sa.JSON(), nullable=True),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("error", sa.String(length=200), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('ok', 'error')", name=op.f("ck_audit_runs_status")),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_audit_runs_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_runs")),
    )
    with op.batch_alter_table("audit_runs", schema=None) as batch_op:
        batch_op.create_index("ix_audit_runs_created_at", ["created_at"], unique=False)

    op.create_table(
        "memory_facts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(length=200), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_memory_facts_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_facts")),
    )
    with op.batch_alter_table("memory_facts", schema=None) as batch_op:
        batch_op.create_index("ix_memory_facts_user_id", ["user_id"], unique=False)

    op.create_table(
        "notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("review_reason", sa.String(length=64), nullable=True),
        sa.Column("source_text", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_notes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notes")),
    )
    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.create_index("ix_notes_user_id", ["user_id"], unique=False)

    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("tags_json", sa.JSON(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("review_reason", sa.String(length=64), nullable=True),
        sa.Column("source_text", sa.String(length=4000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high')", name=op.f("ck_tasks_priority")),
        sa.CheckConstraint(
            "status IN ('todo', 'in_progress', 'done')", name=op.f("ck_tasks_status")
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_tasks_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.create_index("ix_tasks_user_id_status", ["user_id", "status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_index("ix_tasks_user_id_status")
    op.drop_table("tasks")

    with op.batch_alter_table("notes", schema=None) as batch_op:
        batch_op.drop_index("ix_notes_user_id")
    op.drop_table("notes")

    with op.batch_alter_table("memory_facts", schema=None) as batch_op:
        batch_op.drop_index("ix_memory_facts_user_id")
    op.drop_table("memory_facts")

    with op.batch_alter_table("audit_runs", schema=None) as batch_op:
        batch_op.drop_index("ix_audit_runs_created_at")
    op.drop_table("audit_runs")

    op.drop_table("users")
