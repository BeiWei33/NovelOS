"""Initial migration: create all canonical and projection tables.

Revision ID: 001
Revises:
Create Date: 2026-07-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Novel
    op.create_table(
        "novel",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Chapter
    op.create_table(
        "chapter",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("novel_id", UUID, sa.ForeignKey("novel.id"), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("planning", JSONB, nullable=False, server_default="{}"),
        sa.Column("summary", JSONB, nullable=False, server_default="{}"),
        sa.Column("consistency", JSONB, nullable=False, server_default="{}"),
        sa.Column("chapter_facts", JSONB, nullable=False, server_default="{}"),
        sa.Column("metadata", JSONB, nullable=False, server_default='{"status": "draft"}'),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_chapter_novel_order", "chapter", ["novel_id", "order"], unique=True)

    # Scene
    op.create_table(
        "scene",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("chapter_id", UUID, sa.ForeignKey("chapter.id"), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("planning", JSONB, nullable=False, server_default="{}"),
        sa.Column("document", JSONB, nullable=False, server_default='{"blocks": []}'),
        sa.Column("body_history", JSONB, nullable=False, server_default="{}"),
        sa.Column("provenance", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_scene_chapter_order", "scene", ["chapter_id", "order"], unique=True)

    # Character
    op.create_table(
        "character",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("novel_id", UUID, sa.ForeignKey("novel.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("age", sa.Integer, nullable=True),
        sa.Column("occupation", sa.String(255), nullable=True),
        sa.Column("personality", JSONB, nullable=False, server_default="[]"),
        sa.Column("goal", sa.Text, nullable=True),
        sa.Column("fear", sa.Text, nullable=True),
        sa.Column("habit", JSONB, nullable=False, server_default="[]"),
        sa.Column("speech_style", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # World
    op.create_table(
        "world",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("novel_id", UUID, sa.ForeignKey("novel.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # Style
    op.create_table(
        "style",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("novel_id", UUID, sa.ForeignKey("novel.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("profile", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # NarrativeEvent
    op.create_table(
        "narrative_event",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scene_id", UUID, sa.ForeignKey("scene.id"), nullable=False),
        sa.Column("type", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("target", sa.String(255), nullable=True),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("sequence", sa.Integer, nullable=False),
    )

    # SceneArtifact
    op.create_table(
        "scene_artifact",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scene_id", UUID, sa.ForeignKey("scene.id"), nullable=False, unique=True),
        sa.Column("scene_version", sa.Integer, nullable=False),
        sa.Column("facts", JSONB, nullable=False, server_default="{}"),
        sa.Column("narrative_events", JSONB, nullable=False, server_default="[]"),
        sa.Column("summary", JSONB, nullable=False, server_default="{}"),
        sa.Column("keywords", JSONB, nullable=False, server_default="[]"),
        sa.Column("emotion_profile", JSONB, nullable=False, server_default="{}"),
        sa.Column("entities", JSONB, nullable=False, server_default="[]"),
        sa.Column("foreshadow_hints", JSONB, nullable=False, server_default="[]"),
        sa.Column("timeline_deltas", JSONB, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # ChapterArtifact
    op.create_table(
        "chapter_artifact",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("chapter_id", UUID, sa.ForeignKey("chapter.id"), nullable=False, unique=True),
        sa.Column("summary", JSONB, nullable=False, server_default="{}"),
        sa.Column("facts", JSONB, nullable=False, server_default="{}"),
        sa.Column("consistency", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    # --- Projection tables ---
    op.create_table(
        "fact_projection",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scene_id", UUID, nullable=False),
        sa.Column("fact_type", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255)),
        sa.Column("target", sa.String(255)),
        sa.Column("payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("sequence", sa.Integer, nullable=False),
    )
    op.create_index("ix_fact_projection_scene", "fact_projection", ["scene_id"])
    op.create_index("ix_fact_projection_actor", "fact_projection", ["actor"])

    op.create_table(
        "character_state_projection",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("character_id", UUID, nullable=False),
        sa.Column("novel_id", UUID, nullable=False),
        sa.Column("chapter_id", UUID, nullable=True),
        sa.Column("scene_id", UUID, nullable=True),
        sa.Column("state", JSONB, nullable=False, server_default="{}"),
        sa.Column("arc_summary", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_character_state_char", "character_state_projection", ["character_id"])
    op.create_index("ix_character_state_novel", "character_state_projection", ["novel_id"])

    op.create_table(
        "relationship_projection",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("character_a", sa.String(255), nullable=False),
        sa.Column("character_b", sa.String(255), nullable=False),
        sa.Column("novel_id", UUID, nullable=False),
        sa.Column("trust", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("affection", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("fear", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="neutral"),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )
    op.create_index("ix_relationship_novel", "relationship_projection", ["novel_id"])
    op.create_index("ix_relationship_pair", "relationship_projection", ["character_a", "character_b"])

    op.create_table(
        "timeline_projection",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("chapter_id", UUID, nullable=False),
        sa.Column("scene_id", UUID, nullable=False),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("narrative_time", sa.String(100), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=True),
        sa.Column("event_summary", sa.Text, nullable=True),
        sa.Column("characters", ARRAY(sa.Text), nullable=False, server_default="{}"),
    )
    op.create_index(
        "ix_timeline_chapter",
        "timeline_projection",
        ["chapter_id", "scene_id", "sequence"],
    )

    op.create_table(
        "retrieval_projection",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("scene_id", UUID, nullable=False, unique=True),
        sa.Column("chapter_id", UUID, nullable=False),
        sa.Column("one_line", sa.Text, nullable=True),
        sa.Column("keywords", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("block_types", ARRAY(sa.Text), nullable=False, server_default="{}"),
    )
    op.create_index("ix_retrieval_scene", "retrieval_projection", ["scene_id"])


def downgrade() -> None:
    op.drop_table("retrieval_projection")
    op.drop_table("timeline_projection")
    op.drop_table("relationship_projection")
    op.drop_table("character_state_projection")
    op.drop_table("fact_projection")
    op.drop_table("chapter_artifact")
    op.drop_table("scene_artifact")
    op.drop_table("narrative_event")
    op.drop_table("style")
    op.drop_table("world")
    op.drop_table("character")
    op.drop_table("scene")
    op.drop_table("chapter")
    op.drop_table("novel")