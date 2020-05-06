import asyncio

import pytest

from tests.utils import get_fixtures_data


@pytest.fixture(autouse=True)
def loop_factory():
    return asyncio.new_event_loop


def pytest_runtest_setup(item):
    if "run_loop" in item.keywords and "loop" not in item.fixturenames:
        # inject an event loop fixture for all async tests which don't use async fixture,
        # in this case loop won't initialize itself
        item.fixturenames.append("loop")


@pytest.fixture(scope="session")
def get_fixtures_by_name(db_fixtures):
    def _get_fixtures(name: str):
        return db_fixtures[name]

    return _get_fixtures


@pytest.fixture(scope="session")
def db_fixtures():
    return get_fixtures_data()


@pytest.fixture(scope="session")
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@test.com",
        "phone": "+123456789",
        "password": "test_pwd"
    }
