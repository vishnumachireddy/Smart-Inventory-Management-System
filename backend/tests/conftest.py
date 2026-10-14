import os
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set testing environment before importing app modules
os.environ["TESTING"] = "1"
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models import User, Category, Supplier, Product, InventoryBatch
from app.main import app

# In-memory SQLite specifically for rapid, isolated unit testing suite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a transactional database session per test function, rebuilding schema each time."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Provides FastAPI TestClient overriding get_db with test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def owner_user(db_session):
    """Creates a sample Shop Owner user."""
    user = User(
        email="test_owner@stocksense.com",
        hashed_password=get_password_hash("Owner@123"),
        full_name="Test Shop Owner",
        role="shop_owner",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def staff_user(db_session):
    """Creates a sample Staff user."""
    user = User(
        email="test_staff@stocksense.com",
        hashed_password=get_password_hash("Staff@123"),
        full_name="Test Staff Worker",
        role="staff",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def owner_headers(owner_user):
    token = create_access_token(subject=owner_user.id, role=owner_user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def staff_headers(staff_user):
    token = create_access_token(subject=staff_user.id, role=staff_user.role)
    return {"Authorization": f"Bearer {token}"}
