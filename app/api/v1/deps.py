"""API dependencies for auth and rate limiting."""
from typing import Optional, Dict, List
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.models.user import User, UserRole
from app.core.config import settings
from collections import defaultdict
from datetime import datetime, timedelta


# Simple in-memory rate limiter (use Redis in production)
_rate_limit_store: Dict[str, List[datetime]] = defaultdict(list)


def get_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")) -> str:
    """
    Validate API key from header.

    Args:
        x_api_key: API key from header

    Returns:
        API key string

    Raises:
        HTTPException if key is invalid
    """
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def rate_limit(api_key: str = Depends(get_api_key)):
    """
    Simple rate limiter (per API key).

    Args:
        api_key: Validated API key

    Raises:
        HTTPException if rate limit exceeded
    """
    now = datetime.now()
    minute_ago = now - timedelta(minutes=1)

    # Clean old entries
    _rate_limit_store[api_key] = [
        ts for ts in _rate_limit_store[api_key] if ts > minute_ago
    ]

    # Check limit
    if len(_rate_limit_store[api_key]) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {settings.RATE_LIMIT_PER_MINUTE} requests per minute."
        )

    # Record request
    _rate_limit_store[api_key].append(now)
    return api_key


def get_current_user(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> User:
    """
    Get current user from API key (simplified - in production, use JWT tokens).

    Args:
        db: Database session
        api_key: Validated API key

    Returns:
        User object

    Raises:
        HTTPException if user not found
    """
    # TODO: Implement proper user lookup from API key
    # For now, return a default user
    user = db.query(User).filter(User.email == "api@vbi.local").first()
    if not user:
        # Create default API user if doesn't exist
        user = User(
            email="api@vbi.local",
            hashed_password="",  # Not used for API key auth
            role=UserRole.ACCREDITED_AGENT,  # Default role
            can_view_phi=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

