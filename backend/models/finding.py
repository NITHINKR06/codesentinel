from sqlalchemy import Column, String, Integer, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base
import uuid


class Finding(Base):
    __tablename__ = "findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)

    vuln_type = Column(String, nullable=False)   # sqli, xss, hardcoded_secret, etc.
    severity = Column(String, nullable=False)     # critical, high, medium, low
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=True)
    function_name = Column(String, nullable=True)

    title = Column(String, nullable=False)
    description = Column(String, nullable=False)   # plain English
    plain_impact = Column(String, nullable=True)   # "attacker can steal all passwords in 2 steps"

    vulnerable_code = Column(String, nullable=True)
    poc_exploit = Column(String, nullable=True)

    mitre_technique = Column(String, nullable=True)   # e.g. T1190
    mitre_tactic = Column(String, nullable=True)

    extra = Column(JSON, default=dict)
