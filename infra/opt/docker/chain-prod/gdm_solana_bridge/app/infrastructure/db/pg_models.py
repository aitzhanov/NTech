from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "gdm_transactions"

    id = Column(Integer, primary_key=True)
    request_id = Column(String, unique=True, index=True, nullable=False)
    correlation_id = Column(String, index=True)
    entity_type = Column(String)
    entity_id = Column(String)
    action = Column(String)

    payload_hash = Column(String, nullable=False)
    payload = Column(JSON)

    status = Column(String, index=True)
    business_version = Column(Integer, default=1)
    tx_hash = Column(String, index=True)

    error_code = Column(String)

    version = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "gdm_audit_logs"

    id = Column(Integer, primary_key=True)
    request_id = Column(String, index=True)
    correlation_id = Column(String, index=True)

    entity_type = Column(String)
    entity_id = Column(String)
    action = Column(String)

    payload_hash = Column(String)
    transaction_id = Column(String)
    transaction_lifecycle = Column(String)
    blockchain_tx_hash = Column(String)

    result_status = Column(String)
    error_code = Column(String)

    decision_id = Column(String)
    warnings = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
