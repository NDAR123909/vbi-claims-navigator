"""Audit logging utilities."""
from sqlalchemy.orm import Session
from app.models.claim import AuditLog
from datetime import datetime
from typing import Optional, Dict, Any


def log_audit(
    db: Session,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event.

    Args:
        db: Database session
        user_id: User ID performing action
        action: Action name (e.g., "view_client", "create_claim")
        resource_type: Type of resource (e.g., "client", "claim")
        resource_id: Optional resource ID
        ip_address: Optional IP address
        user_agent: Optional user agent string
        reason: Optional reason for access
        metadata: Optional additional metadata
    """
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        reason=reason,
        metadata=metadata
    )
    db.add(audit_entry)
    db.commit()

