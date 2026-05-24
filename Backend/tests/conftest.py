import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_gouseshop.db")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("USE_FAKE_EXTERNAL_SERVICES", "true")

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from app.core.database import engine
from app.models import Base
from main import app


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
def client():
    return TestClient(app)
