from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base
import uuid


class Patch(Base):
    __tablename__ = "patches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)

    file_path = Column(String, nullable=False)
    original_code = Column(String, nullable=False)
    patched_code = Column(String, nullable=False)

    validated = Column(Boolean, default=False)
    validation_attempts = Column(String, default="0")
    validation_notes = Column(String, nullable=True)

    applied_to_pr = Column(Boolean, default=False)
