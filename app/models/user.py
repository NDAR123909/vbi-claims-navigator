"""User model with RBAC."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum
from app.db.base import Base


class UserRole(str, enum.Enum):
    """User roles for RBAC."""
    READER = "reader"
    EDITOR = "editor"
    ACCREDITED_AGENT = "accredited_agent"
    ADMIN = "admin"


class User(Base):
    """User model with role-based access control."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.READER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    can_view_phi = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        role_permissions = {
            UserRole.READER: ["read"],
            UserRole.EDITOR: ["read", "write"],
            UserRole.ACCREDITED_AGENT: ["read", "write", "finalize"],
            UserRole.ADMIN: ["read", "write", "finalize", "admin"],
        }
        return permission in role_permissions.get(self.role, [])

