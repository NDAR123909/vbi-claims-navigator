"""Pytest configuration and fixtures."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.base import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.client import Client
from app.utils.security import encrypt_field
from datetime import date

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@vbi.local",
        hashed_password="test",
        full_name="Test User",
        role=UserRole.ACCREDITED_AGENT,
        can_view_phi=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_client_record(db_session):
    """Create a test client record."""
    client = Client(
        first_name_encrypted=encrypt_field("Test"),
        last_name_encrypted=encrypt_field("Client"),
        ssn_encrypted=encrypt_field("111-22-3333"),
        date_of_birth=date(1990, 1, 1),
        client_number="TEST-001",
        branch_of_service="US Army"
    )
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    return client

