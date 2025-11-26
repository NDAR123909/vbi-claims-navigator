"""Client model for storing veteran client information."""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.db.base import Base


class Client(Base):
    """Client model - stores veteran client information with encrypted PII/PHI."""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    # Encrypted fields (encrypted at application level)
    first_name_encrypted = Column(String, nullable=False)
    last_name_encrypted = Column(String, nullable=False)
    ssn_encrypted = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    # Non-sensitive metadata
    client_number = Column(String, unique=True, index=True, nullable=False)
    branch_of_service = Column(String, nullable=True)
    service_start_date = Column(Date, nullable=True)
    service_end_date = Column(Date, nullable=True)
    # Additional metadata
    metadata = Column(JSON, nullable=True)  # For flexible additional data
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

