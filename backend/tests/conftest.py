import sys
import os

os.environ["ENVIRONMENT"] = "test"
os.environ["POSTGRES_PASSWORD"] = "fake"
os.environ["POSTGRES_USER"] = "fake"
os.environ["POSTGRES_HOST"] = "fake"
os.environ["POSTGRES_DB"] = "fake"

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Убиваем рейт лимитер ДО импорта main
import slowapi.extension
slowapi.extension.Limiter.limit = lambda self, limit_str: lambda func: func

from main import app
from database import Base, get_db
from models import User, Visitor, RefreshToken, Log
from utils import get_password_hash
from .test_config import ADMIN_PASSWORD, SECRETARY_PASSWORD, GUARD_PASSWORD

TEST_DB = "test.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

if os.path.exists(TEST_DB):
    os.remove(TEST_DB)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

if hasattr(app.state, 'limiter'):
    app.state.limiter.enabled = False

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_users():
    db = TestingSessionLocal()
    db.query(User).delete()
    db.add(User(username="admin", hashed_password=get_password_hash(ADMIN_PASSWORD),
                full_name="Admin Test", role="admin", is_admin=True))
    db.add(User(username="secretary", hashed_password=get_password_hash(SECRETARY_PASSWORD),
                full_name="Secretary Test", role="secretary", is_admin=False))
    db.add(User(username="guard", hashed_password=get_password_hash(GUARD_PASSWORD),
                full_name="Guard Test", role="guard", is_admin=False))
    db.commit()
    yield
    for table in reversed(Base.metadata.sorted_tables):
        db.execute(table.delete())
    db.commit()
    db.close()