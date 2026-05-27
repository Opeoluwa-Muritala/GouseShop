import os
from urllib.parse import urlsplit

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("USE_FAKE_EXTERNAL_SERVICES", "true")

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.core.config import settings
from app.core.database import engine
from app.core.redis import delete_keys_with_prefix
from app.models import Base
from main import app


def pytest_configure(config):
    config.addinivalue_line("markers", "db: reset the test database for this test")


def _database_name() -> str:
    return urlsplit(settings.sqlalchemy_database_url).path.rsplit("/", 1)[-1].lower()


def _assert_online_test_database_is_safe() -> None:
    database_url = settings.sqlalchemy_database_url.lower()
    if database_url.startswith("sqlite"):
        pytest.fail("DATABASE_URL must point to the online test database, not SQLite.")
    if "test" not in _database_name():
        pytest.fail("Refusing to reset a database whose name does not contain 'test'.")


def _assert_test_redis_is_safe() -> None:
    if settings.use_fake_redis:
        pytest.fail("USE_FAKE_REDIS=false is required for DB tests.")
    if not settings.redis_key_prefix.startswith("test:"):
        pytest.fail("REDIS_KEY_PREFIX must start with 'test:' for test cleanup.")


@pytest_asyncio.fixture(autouse=True)
async def reset_db(request):
    if request.node.get_closest_marker("db") is None:
        yield
        return
    _assert_online_test_database_is_safe()
    _assert_test_redis_is_safe()
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(delete(table))
    await delete_keys_with_prefix(settings.redis_key_prefix)
    yield
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(delete(table))
    await delete_keys_with_prefix(settings.redis_key_prefix)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def fast_password_hashing(monkeypatch):
    def hash_password(password: str) -> str:
        return f"test-hash:{password}"

    def verify_password(password: str, password_hash: str) -> bool:
        return password_hash == hash_password(password)

    monkeypatch.setattr("app.services.auth_service.hash_password", hash_password)
    monkeypatch.setattr("app.services.auth_service.verify_password", verify_password)
