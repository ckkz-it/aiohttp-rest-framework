import pytest

from tests.utils import get_fixtures_data


@pytest.fixture
def users_fixtures():
    return get_fixtures_data()["users"]


@pytest.fixture
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@test.com",
        "phone": "+123456789",
        "password": "test_pwd"
    }
