"""Shared pytest configuration."""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--require-postgres",
        action="store_true",
        help="fail instead of skip when SIGNALFORGE_TEST_DATABASE_URL is absent",
    )


@pytest.fixture
def postgres_engine(pytestconfig: pytest.Config) -> Iterator[Engine]:
    """Apply migrations to a disposable PostgreSQL database."""
    database_url = os.environ.get("SIGNALFORGE_TEST_DATABASE_URL")
    if not database_url:
        if bool(pytestconfig.getoption("--require-postgres")):
            pytest.fail("SIGNALFORGE_TEST_DATABASE_URL is required for the PostgreSQL profile")
        pytest.skip("PostgreSQL integration profile not requested")

    previous_url = os.environ.get("SIGNALFORGE_DATABASE_URL")
    os.environ["SIGNALFORGE_DATABASE_URL"] = database_url
    config = Config("alembic.ini")
    engine = create_engine(database_url)
    try:
        command.downgrade(config, "base")
        command.upgrade(config, "head")
        yield engine
        command.downgrade(config, "base")
    finally:
        engine.dispose()
        if previous_url is None:
            os.environ.pop("SIGNALFORGE_DATABASE_URL", None)
        else:
            os.environ["SIGNALFORGE_DATABASE_URL"] = previous_url
