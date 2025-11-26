"""Database session utilities."""
from app.db.base import SessionLocal


def get_db_session():
    """Get a database session."""
    return SessionLocal()

