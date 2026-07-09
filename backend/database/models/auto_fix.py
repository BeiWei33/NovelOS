"""
Auto-Fix database models — backup and log tables for the auto-fix pipeline.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import JSONB, UUID

from database.session import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


class AutoFixBackup(Base):
    """Backup of original file content before auto-fix patch."""

    __tablename__ = "auto_fix_backup"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    patch_id = Column(UUID(as_uuid=False), nullable=False)
    file_path = Column(Text, nullable=False)
    original_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_auto_fix_backup_patch", "patch_id"),
    )


class AutoFixLog(Base):
    """Log of auto-fix operations for audit trail."""

    __tablename__ = "auto_fix_log"

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    patch_id = Column(UUID(as_uuid=False), nullable=False)
    error_id = Column(UUID(as_uuid=False), nullable=False)
    error_fingerprint = Column(String(64), nullable=False)
    fix_strategy = Column(Text, nullable=False)
    modified_files = Column(JSONB, default=list, nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending, applied, verified, failed, rolled_back
    verified = Column(JSONB, default=dict, nullable=False)  # {tsc: bool, eslint: bool, test: bool}
    commit_hash = Column(String(40), nullable=True)
    push_status = Column(String(20), nullable=True)  # pending, pushed, failed
    rollback_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_auto_fix_log_patch", "patch_id"),
        Index("ix_auto_fix_log_error", "error_id"),
        Index("ix_auto_fix_log_status", "status"),
    )


__all__ = [
    "AutoFixBackup",
    "AutoFixLog",
]