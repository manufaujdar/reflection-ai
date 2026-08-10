import os

os.environ["REFLECTION_DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from reflection_ai import api
from reflection_ai.db import Base, get_db
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def client():
    from sqlalchemy import create_engine

    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    local = sessionmaker(bind=engine, expire_on_commit=False)

    def override():
        with local() as session:
            yield session

    api.app.dependency_overrides[get_db] = override
    with TestClient(api.app) as test_client:
        yield test_client
    api.app.dependency_overrides.clear()
