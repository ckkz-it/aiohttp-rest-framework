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
def users_fixtures(get_fixtures_by_name):
    return get_fixtures_by_name("users")


@pytest.fixture(scope="session")
def get_fixtures_by_name():
    def _get_fixtres(name: str):
        return get_fixtures_data()[name]

    return _get_fixtres


@pytest.fixture(scope="session")
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@test.com",
        "phone": "+123456789",
        "password": "test_pwd"
    }
