"""
RewriteSample model and embedding service.

Good writing examples to inject into Writer Skills.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID

from database.session import Base


def new_uuid() -> str:
    import uuid
    return str(uuid.uuid4())


class RewriteSample(Base):
    """Good writing examples for reference during generation."""

    __tablename__ = "rewrite_sample"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    novel_id = Column(UUID(as_uuid=False), nullable=True)  # Optional: can be global

    input_text = Column(Text, nullable=False)   # Original text or description
    output_text = Column(Text, nullable=False)  # Improved/good version
    tags = Column(JSONB, default=list)          # e.g., ["dialogue", "emotion"]
    style_tags = Column(JSONB, default=list)    # e.g., ["suspense", "romantic"]

    embedding = Column(JSONB, nullable=True)    # Vector stored as list[float]

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_rewrite_sample_novel", "novel_id"),
    )