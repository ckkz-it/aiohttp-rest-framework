import pytest

from tests.utils import get_fixtures_data


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
