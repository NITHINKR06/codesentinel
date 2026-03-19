from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import types
from db.database import Base
from datetime import datetime
import uuid
import enum


# Cross-DB UUID that works with both SQLite and Postgres
class UUID(types.TypeDecorator):
    impl = types.String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(value)


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    SCANNING = "scanning"
    CHAINING = "chaining"
    GENERATING = "generating"
    PATCHING = "patching"
    VALIDATING = "validating"
    SCORING = "scoring"
    COMPLETE = "complete"
    FAILED = "failed"


class ScanType(str, enum.Enum):
    GITHUB = "github"
    ZIP = "zip"
    URL = "url"


class Scan(Base):
    __tablename__ = "scans"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    status = Column(String, default=ScanStatus.PENDING, nullable=False)
    scan_type = Column(String, nullable=False)

    # Input
    github_url = Column(String, nullable=True)
    live_url = Column(String, nullable=True)
    repo_name = Column(String, nullable=True)

    # Results summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)

    # Scores
    score_before = Column(Integer, nullable=True)
    score_after = Column(Integer, nullable=True)

    # Full data stored as JSON strings
    findings_data = Column(JSON, default=list)
    chains_data = Column(JSON, default=list)
    patches_data = Column(JSON, default=list)
    ghost_commits_data = Column(JSON, default=list)
    threat_actor_data = Column(JSON, nullable=True)
    attack_graph_data = Column(JSON, nullable=True)

    # Naive datetimes (no timezone) — works with SQLite and Postgres
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

    # GitHub PR
    pr_url = Column(String, nullable=True)
    pr_number = Column(Integer, nullable=True)