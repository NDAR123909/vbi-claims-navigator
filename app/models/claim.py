"""Claim and document models."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, JSON, Float, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Claim(Base):
    """Claim model - represents a VA claim."""
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    claim_type = Column(String, nullable=False)  # e.g., "PTSD", "Tinnitus", etc.
    status = Column(String, default="draft", nullable=False)  # draft, submitted, approved, denied
    draft_text = Column(Text, nullable=True)
    evidence_map = Column(JSON, nullable=True)  # List of {doc_id, excerpt, supporting_section}
    confidence_score = Column(Float, nullable=True)
    human_review_required = Column(Boolean, default=True, nullable=False)
    template_used = Column(String, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    finalized_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    client = relationship("Client", backref="claims")
    documents = relationship("ClaimDocument", back_populates="claim", cascade="all, delete-orphan")


class ClaimDocument(Base):
    """Document associated with a claim."""
    __tablename__ = "claim_documents"

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False, index=True)
    document_type = Column(String, nullable=False)  # e.g., "DD214", "C&P Exam", "MRI Report"
    file_path = Column(String, nullable=True)  # Path in object storage
    file_name = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    ocr_text = Column(Text, nullable=True)  # Extracted text from OCR
    extracted_data = Column(JSON, nullable=True)  # Structured extracted data
    vector_id = Column(String, nullable=True)  # ID in vector DB
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    claim = relationship("Claim", back_populates="documents")


class AuditLog(Base):
    """Audit log for PHI access and actions."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False)  # e.g., "view_client", "create_claim", "access_phi"
    resource_type = Column(String, nullable=False)  # e.g., "client", "claim", "document"
    resource_id = Column(Integer, nullable=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

